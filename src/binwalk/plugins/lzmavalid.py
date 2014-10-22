import lzma
import binwalk.core.plugin
from binwalk.core.common import BlockFile

class LZMAPlugin(binwalk.core.plugin.Plugin):
    '''
    Validates lzma signature results.
    '''
    MODULES = ['Signature']

    # Some lzma files exclude the file size, so we have to put it back in.
    # See also the lzmamod.py plugin.
    FAKE_LZMA_SIZE = "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"

    # Check up to the first 64KB
    MAX_DATA_SIZE = 64 * 1024

    def is_valid_lzma(self, data):
        valid = True

        # The only acceptable exception is that of IOError "unknown BUF error",
        # which indicates that the input data was truncated.
        try:
            d = lzma.decompress(data)
        except IOError as e:
            if e.message != "unknown BUF error":
                valid = False
        except Exception as e:
            valid = False

        return valid

    def scan(self, result):
        # If this result is an lzma signature match, try to decompress the data
        if result.valid and result.file and result.description.lower().startswith('lzma compressed data'):

            # Seek to and read the suspected lzma data
            fd = self.module.config.open_file(result.file.name, offset=result.offset, length=self.MAX_DATA_SIZE)
            data = fd.read(self.MAX_DATA_SIZE)
            fd.close()

            # Validate the original data; if that fails, maybe it is missing the size field,
            # so try again with a dummy size field in place.
            if not self.is_valid_lzma(data):
                data = data[:5] + self.FAKE_LZMA_SIZE + data[5:]
                if not self.is_valid_lzma(data):
                    result.valid = False

