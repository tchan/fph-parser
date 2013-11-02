#!/usr/bin/env python2.7

# Fisher and Paykel CPAP .FPH file parser.
#
# http://sourceforge.net/apps/mediawiki/sleepyhead/index.php?title=Icon
#
# Done: SUM*.fph files.
#

from struct import calcsize, unpack
from collections import namedtuple
from datetime import datetime

def parseFile(filename):
	parts = filename.split('/')

	prefix = parts[-1][0:3]

	if (prefix == 'SUM'):
		return SummaryFile(filename)
	else:
		return FPHFile(filename)



class FPHFile:
	FPH_MAGIC_NUMBER = '0201'

	HEADER_SIZE = 0x200
	HEADER_SEPARATOR = '\r'
	# Header (field name, offset) tuples
	HEADER_OFFSETS = [
		('version', 1),
		('filename', 2),
		('serialnumber', 3),
		('series', 4),
		('model', 5)
	]

	Header = namedtuple('Header', [x[0] for x in HEADER_OFFSETS])

	CSV_SEPARATOR = ';'

	records = None

	def __init__(self, filename):
		with open(filename, 'rb') as f:
			self.raw = f
			self.header = self._parseHeader(self.raw)

			self._parseBody()

	def _parseBody(self):
		pass

	def _parseHeader(self, f):
		fields = f.read(self.HEADER_SIZE).split(self.HEADER_SEPARATOR)

		if (fields[0] != self.FPH_MAGIC_NUMBER):
			raise self.FPH_MAGIC_NUMBER + " magic number not found"

		# last byte (fields[6][-1]) contains a checksum,
		# TODO figure out how to calculate it and check.

		return self.Header._make(
			[fields[offset] for name, offset in self.HEADER_OFFSETS]
		)

	def _parseTimestamp(self, raw):
		dateword, timeword = unpack('<HH', raw)

		year = 2000 + ((dateword >> 9) & 0x7f)
		month = (dateword >> 5) & 0x0f
		day = dateword & 0x1f

		hour = (timeword >> 11) & 0x1f
		minute = (timeword >> 5) & 0x3f
		second = (timeword & 0x1f) * 2

		return datetime(year, month, day, hour, minute, second)

	def _parseDuration(self, raw):
		return raw * 3.6

	def toCSV(self):
		pass

	def __str__(self, showHeader=False):
		ret = ''
		if (showHeader):
			ret += str(self.header) + '\n'

		if (self.records and len(self.records) > 0):
			ret += self.CSV_SEPARATOR.join(self.records[0]._fields) + '\n'
			ret += '\n'.join([self.CSV_SEPARATOR.join(map(str, r)) for r in self.records])

		return ret


class SummaryFile(FPHFile):

	SUMMARY_RECORD_SIZE = 0x1d
	SUMMARY_RECORD = (
		('timestamp', '4s'),
		('runtime', 'B'),
		('usage', 'B'),
		('_', '7s'),
		('leak90', 'H'),
		('lowPressure', 'B'),
		('highPressure', 'B'),
		('_', 's'),
		('apneaEvents', 'B'),
		('hypoapneaEvents', 'B'),
		('flowlimitiationEvents', 'B'),
		('_', '3s'),
		('pressure1', 'B'),
		('pressure2', 'B'),
		('_', '2s'),
		('humiditySetting', 'B')
	)

	SummaryRecord = namedtuple('SummaryRecord',
		[x[0] for x in SUMMARY_RECORD if x[0] != '_']
	)

	def _parseBody(self):
		f = self.raw
		f.seek(self.HEADER_SIZE)

		record = f.read(self.SUMMARY_RECORD_SIZE)
		self.records = []

		for i in range(8):
			self.records.append(self._parseRecord(record))
			record = f.read(self.SUMMARY_RECORD_SIZE)

	def _parseRecord(self, record):

		transforms = {
			'timestamp': self._parseTimestamp,
			'runtime': self._parseDuration,
			'usage': self._parseDuration
		}

		offset = 0
		values = []
		for (name, format) in self.SUMMARY_RECORD:
			format = '<' + format
			size = calcsize(format)
			raw = record[offset:(offset + size)]

			if (name != '_'):
				value = unpack(format, raw)[0]
				if name in transforms:
					value = transforms[name](value)

				values.append(value)

			offset += size

		return self.SummaryRecord._make(values)





