import numpy as np

def calc_fall_winter_baseflow(flow_matrix, fall_wet_timings, spring_timings):
    wet_baseflows_10 = []
    wet_baseflows_50 = []
    wet_bfl_durs = []
    hfa_ROC_daily = []
    hfa_ROC_1090 = []
    for column_number, spring_date in enumerate(spring_timings):
        if spring_date and fall_wet_timings[column_number] and not np.isnan(spring_date) and not np.isnan(fall_wet_timings[column_number]):
            if fall_wet_timings[column_number] and spring_date > fall_wet_timings[column_number]:
                flow_data = flow_matrix[int(fall_wet_timings[column_number]):int(spring_date), column_number]
            else:
                flow_data = []
        else:
            flow_data = []

        flow_data = list(flow_data)
        if flow_data:
            wet_baseflows_10.append(np.nanpercentile(flow_data, 10))
            wet_baseflows_50.append(np.nanpercentile(flow_data, 50))
            wet_bfl_durs.append(len(flow_data))
            # Calc ROC for high flow ascension, positive daily median change
            daily_roc = []
            for flow_index, data in enumerate(flow_data):
                if flow_index == len(flow_data) - 1:
                    continue
                elif flow_data[flow_index + 1] > flow_data[flow_index]: # record positive daily change only
                    daily_roc.append(
                        (flow_data[flow_index + 1] - flow_data[flow_index]) / flow_data[flow_index]) # percentage units
            hfa_ROC_daily.append(np.nanmedian(daily_roc))
            # Calc ROC for high flow ascension, 10th to 90th slope
            tenth = np.nanpercentile(flow_data, 10)
            nintieth = np.nanpercentile(flow_data, 90)
            hfa_ROC_1090.append(
                (nintieth - tenth) / (spring_timings[column_number] - fall_wet_timings[column_number])) # units of cfs/day

        else:
            wet_baseflows_10.append(None)
            wet_baseflows_50.append(None)
            wet_bfl_durs.append(None)
            hfa_ROC_daily.append(None)
            hfa_ROC_1090.append(None)
    return wet_baseflows_10, wet_baseflows_50, wet_bfl_durs, hfa_ROC_daily, hfa_ROC_1090
