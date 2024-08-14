import struct
from collections import namedtuple

import numpy as np 
import pandas as pd

# class inefficiently reads in and stores data in a pandas dataframe
# matches the structs in ross/core/instrumentation/st-instrumentation.h
# with each row in the df being an instance of the struct
# TODO: need a way to pull in model data
class ROSSFile:
    def __init__(self, filename):
        self.f = open(filename, "rb")

        self.engine_md_format = "@2i2d"
        self.engine_md_size = struct.calcsize(self.engine_md_format)

        self.engine_pe_format = "@13I13f"
        self.engine_pe_size = struct.calcsize(self.engine_pe_format)

        self.engine_kp_format = "@9I2f"
        self.engine_kp_size = struct.calcsize(self.engine_kp_format)

        self.engine_lp_format = "@8If"
        self.engine_lp_size = struct.calcsize(self.engine_lp_format)


    def read(self):
        pe_list = []
        kp_list = []
        lp_list = []
        while True:
            md_bytes = self.f.read(self.engine_md_size)
            if not md_bytes:
                break
            md_record = namedtuple("MD", "flag sample_size virtual_time real_time")
            md = md_record._make(struct.unpack(self.engine_md_format, md_bytes))
            #print(f'flag: {md[0]}, sample size: {md[1]}, virtual ts: {md[2]}, real ts: {md[3]}')
            if md.sample_size == self.engine_pe_size:
                #print("found a pe struct")
                pe_bytes = self.f.read(self.engine_pe_size)
                pe_record = namedtuple("PE", "PE_ID events_processed events_aborted events_rolled_back total_rollbacks secondary_rollbacks fossil_collection_attempts pq_queue_size network_sends network_reads number_gvt pe_event_ties all_reduce efficiency network_read_time network_other_time gvt_time fossil_collect_time event_abort_time event_process_time pq_time rollback_time cancel_q_time avl_time buddy_time lz4_time")
                pe_data = pe_record._make(struct.unpack(self.engine_pe_format, pe_bytes))
                df = pd.DataFrame([pe_data])
                df["virtual_time"] = md.virtual_time
                df["real_time"] = md.real_time
                pe_list.append(df)
            elif md.sample_size == self.engine_kp_size:
                #print("found a kp struct")
                kp_bytes = self.f.read(self.engine_kp_size)
                kp_record = namedtuple("KP", "PE_ID KP_ID events_processed events_abort events_rolled_back total_rollbacks secondary_rollbacks network_sends network_reads time_ahead_gvt efficiency")
                kp_data = kp_record._make(struct.unpack(self.engine_kp_format, kp_bytes))
                df = pd.DataFrame([kp_data])
                df["virtual_time"] = md.virtual_time
                df["real_time"] = md.real_time
                kp_list.append(df)
            elif md.sample_size == self.engine_lp_size:
                #print("found a lp struct")
                lp_bytes = self.f.read(self.engine_lp_size)
                lp_record = namedtuple("LP", "PE_ID KP_ID LP_ID events_processed events_abort events_rolled_back network_sends network_reads efficiency")
                lp_data = lp_record._make(struct.unpack(self.engine_lp_format, lp_bytes))
                df = pd.DataFrame([lp_data])
                df["virtual_time"] = md.virtual_time
                df["real_time"] = md.real_time
                lp_list.append(df)
            else:
                print("ERROR: found incorrect struct size")
        self.pe_engine_df = pd.concat(pe_list)
        self.kp_engine_df = pd.concat(kp_list)
        self.lp_engine_df = pd.concat(lp_list)


    def close(self):
        self.f.close()
