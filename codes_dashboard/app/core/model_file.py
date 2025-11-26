import struct
from collections import namedtuple

import pandas as pd

from trame.app.file_upload import ClientFile

#note this actually reads the analysis lps files, which i believe would include engine data as well, if collected
class ModelFile:
    def __init__(self, filename):
        if isinstance(filename, str):
            self.f = open(filename, "rb")
            self.content = self.f.read()
        elif isinstance(filename, ClientFile):
            self.content = filename.content

        self.md_format = "@QLLddii"
        self.md_sz = struct.calcsize(self.md_format)

        # TODO: will need to figure out a way to not hardcode this
        self.simplep2p_format = "@Qlldlld"
        self.simplep2p_size = struct.calcsize(self.simplep2p_format)

        self._use_virtual_time = True
        self._time_variable = "virtual_time"

    def read(self):
        sample_list = []

        byte_pos = 0
        while True:
            md_bytes = self.content[byte_pos:byte_pos+self.md_sz]
            byte_pos += len(md_bytes)
            if not md_bytes:
                break
            md_record = namedtuple("MD", "lp_id kp_id pe_id virtual_time real_time sample_size flag")
            md = md_record._make(struct.unpack(self.md_format, md_bytes))

            # flag == 3 is model data
            if md.flag == 3 and md.sample_size == self.simplep2p_size:
                sp_bytes = self.content[byte_pos:byte_pos+self.simplep2p_size]
                byte_pos += len(sp_bytes)
                sp_record = namedtuple("SimpleP2P", "component_id send_count send_bytes send_time receive_count receive_bytes receive_time")
                sp_data = sp_record._make(struct.unpack(self.simplep2p_format, sp_bytes))
                df = pd.DataFrame([sp_data])
                df["lp_id"] = md.lp_id
                df["virtual_time"] = md.virtual_time
                df["real_time"] = md.real_time
                sample_list.append(df)
            else:
                print(f'sample of size {md.sample_size} found')

        self._simplep2p_df = pd.concat(sample_list)

        self._min_time = self._simplep2p_df[self._time_variable].min()
        self._max_time = self._simplep2p_df[self._time_variable].max()


    def close(self):
        self.f.close()


    @property
    def max_time(self):
        return self._max_time


    @max_time.setter
    def max_time(self, time):
        self._max_time = time
        print(f'max time is {self._max_time}')


    @property
    def min_time(self):
        return self._min_time


    @min_time.setter
    def min_time(self, time):
        self._min_time = time
        print(f'min time is {self._min_time}')

    @property
    def network_df(self):
        return self._simplep2p_df[
            (self._simplep2p_df[self._time_variable] >= self._min_time) & 
            (self._simplep2p_df[self._time_variable] <= self._max_time)]


    def reset_time_range(self):
        print("resetting time range")
        self._min_time = self._simplep2p_df[self._time_variable].min()
        self._max_time = self._simplep2p_df[self._time_variable].max()
        print(f'\tmin time is {self._min_time}')
        print(f'\tmax time is {self._max_time}')


    @property
    def use_virtual_time(self):
        return self._use_virtual_time

    @use_virtual_time.setter
    def use_virtual_time(self, flag):
        self._use_virtual_time = flag
        if self._use_virtual_time:
            self._time_variable = "virtual_time"
        else:
            self._time_variable = "real_time"
        self.reset_time_range()