import numpy as np

def calc_fall_winter_baseflow(flow_matrix, fall_wet_timings, spring_timings, summer_timings):
    wet_baseflows_10 = []
    wet_baseflows_50 = []
    wet_bfl_durs = []
    hfa_ROC_daily = []
    hfa_ROC_1090 = []
    for column_number, spring_date in enumerate(spring_timings):
        if spring_date and fall_wet_timings[column_number] and not np.isnan(spring_date) and not np.isnan(fall_wet_timings[column_number]):
            if fall_wet_timings[column_number] and spring_date > fall_wet_timings[column_number]:
                flow_data_rising = flow_matrix[int(fall_wet_timings[column_number]):int(spring_date), column_number][:]
            else:
                flow_data_rising = []
        else:
            flow_data_rising = []

        flow_data_rising = list(flow_data_rising)

        if flow_data_rising:
            # Calc ROC for high flow ascension, positive daily median change
            daily_roc = []
            for flow_index, data in enumerate(flow_data_rising):
                if flow_index == len(flow_data_rising) - 1:
                    continue
                elif flow_data_rising[flow_index + 1] > flow_data_rising[flow_index] and flow_data_rising[flow_index] > 0: # record positive daily change only
                    daily_roc.append(
                        (flow_data_rising[flow_index + 1] - flow_data_rising[flow_index]) / flow_data_rising[flow_index]) # percentage units
            if len(daily_roc) == 0:
                hfa_ROC_daily.append(None)
            else:
                hfa_ROC_daily.append(np.nanmedian(daily_roc))
            # Calc ROC for high flow ascension, 10th to 90th slope
            tenth = np.nanpercentile(flow_data_rising, 10)
            nintieth = np.nanpercentile(flow_data_rising, 90)
            hfa_ROC_1090.append(
                (nintieth - tenth) / (spring_timings[column_number] - fall_wet_timings[column_number])) # units of cfs/day
        else:
            hfa_ROC_daily.append(None)
            hfa_ROC_1090.append(None)

    for column_number, summer_date in enumerate(summer_timings):
        if summer_date and fall_wet_timings[column_number] and not np.isnan(summer_date) and not np.isnan(fall_wet_timings[column_number]):
            if fall_wet_timings[column_number] and summer_date > fall_wet_timings[column_number]:
                flow_data_hf = flow_matrix[int(fall_wet_timings[column_number]):int(summer_date), column_number][:]
            else:
                flow_data_hf = []
        else:
            flow_data_hf = []
        flow_data_hf = list(flow_data_hf)  

        if flow_data_hf:
            wet_baseflows_10.append(np.nanpercentile(flow_data_hf, 10))
            wet_baseflows_50.append(np.nanpercentile(flow_data_hf, 50))
            wet_bfl_durs.append(len(flow_data_hf))
        else:
            wet_baseflows_10.append(None)
            wet_baseflows_50.append(None)
            wet_bfl_durs.append(None)
            
    return wet_baseflows_10, wet_baseflows_50, wet_bfl_durs, hfa_ROC_daily, hfa_ROC_1090
