
import struct
from collections import namedtuple

import pandas as pd

class EventFile:
    def __init__(self, filename):
        self.f = open(filename, "rb")
        self.md_format = "@IIfffI"
        self.md_sz = struct.calcsize(self.md_format)

        # TODO: will need to figure out a way to not hardcode this
        self.simplep2p_format = "@i"
        self.simplep2p_size = struct.calcsize(self.simplep2p_format)

        self._use_send_time = True
        self._time_variable = "virtual_send"

    def read(self):
        sample_list = []

        while True:
            md_bytes = self.f.read(self.md_sz)
            if not md_bytes:
                break
            md_record = namedtuple("MD", "source_lp dest_lp virtual_send virtual_receive real_times sample_size")
            md = md_record._make(struct.unpack(self.md_format, md_bytes))

            if md.sample_size == self.simplep2p_size:
                sp_bytes = self.f.read(self.simplep2p_size)
                sp_record = namedtuple("SimpleP2P", "event_type")
                sp_data = sp_record._make(struct.unpack(self.simplep2p_format, sp_bytes))
                df = pd.DataFrame([sp_data])
                df["source_lp"] = md.source_lp
                df["dest_lp"] = md.dest_lp
                df["virtual_send"] = md.virtual_send
                df["virtual_receive"] = md.virtual_receive
                sample_list.append(df)
            elif md.sample_size == 0:
                #print(f'source {md.source_lp}, dest {md.dest_lp}')
                continue
            else:
                print(f'sample of size {md.sample_size} found')

        self._simplep2p_df = pd.concat(sample_list)

        self._min_time = self._simplep2p_df[self._time_variable].min()
        self._max_time = self._simplep2p_df[self._time_variable].max()


    def close(self):
        self.f.close()

    #def read_file(self):
    #    self._df = pd.read_csv(self.filename, header=None, names=["LP ID", "Virtual Time", "Packets Sent", "Packets Received", "Bytes Sent", "Bytes Received"])

    #    self._min_time = self._df["Virtual Time"].min()
    #    self._max_time = self._df["Virtual Time"].max()
    #    print(f'min time is {self._min_time}')
    #    print(f'max time is {self._max_time}')

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
    def use_send_time(self):
        return self._use_send_time

    @use_send_time.setter
    def use_send_time(self, flag):
        self._use_send_time = flag
        if self._use_send_time:
            self._time_variable = "virtual_send"
        else:
            self._time_variable = "virtual_receive"
        self.reset_time_range()