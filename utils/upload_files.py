from datetime import datetime
import os
import itertools
import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
from utils.matrix_convert import MatrixConversion
from calculations.AllMetrics import Metrics
from utils.constants import TYPES
from utils.helpers import remove_offset_from_julian_date
from params import summer_params
from params import fall_params
from params import spring_params
from params import winter_params


def upload_files(start_date, files, flow_class):
    output_files = 'user_output_files'

    for file in files:
        gage_name = file.split('/')[1].split('.csv')[0]
        if not os.path.isdir(output_files + '/' + gage_name):
            os.makedirs(output_files + '/' + gage_name)
        file_name = output_files + '/' + gage_name + '/' + gage_name
        dataset = read_csv_to_arrays(file)
        matrix = MatrixConversion(
            dataset['date'], dataset['flow'], start_date)
        
        julian_start_date = datetime.strptime(
            "{}/2001".format(start_date), "%m/%d/%Y").timetuple().tm_yday

        result = get_result(matrix, julian_start_date, int(flow_class))

        write_to_csv(file_name, result, 'annual_flow_matrix')
        write_to_csv(file_name, result, 'drh')
        write_to_csv(file_name, result, 'annual_flow_result')
        write_to_csv(file_name, result, 'parameters', flow_class)
        draw_plots(file_name, result)
        
    return True

def get_result(matrix, julian_start_date, flow_class):

    result = {}
    result["year_ranges"] = [int(i) + 1 for i in matrix.year_array]
    result["flow_matrix"] = np.where(
        pd.isnull(matrix.flow_matrix), None, matrix.flow_matrix).tolist()
    result["start_date"] = matrix.start_date

    calculated_metrics = Metrics(
        matrix.flow_matrix, matrix.years_array, None, None, None, flow_class)

    result["DRH"] = calculated_metrics.drh

    result["all_year"] = {}
    result["all_year"]["average_annual_flows"] = calculated_metrics.average_annual_flows
    result["all_year"]["standard_deviations"] = calculated_metrics.standard_deviations
    result["all_year"]["coefficient_variations"] = calculated_metrics.coefficient_variations
    result["all_year"]["annual_peaks"] = calculated_metrics.annual_peaks

    result["winter"] = {}
    # Convert key from number to names

    key_maps = {50: "fifty", 20: "twenty", 10: "ten", 5: "five", 2: "two"}
    # key_maps = {2: "two", 5: "five", 10: "ten", 20: "twenty", 12: "_two", 15: "_five", 110: "_ten", 120: "_twenty"}

    winter_timings = {}
    winter_durations = {}
    winter_magnitudes = {}
    winter_frequencys = {}
    for key, value in key_maps.items():
        winter_timings[value] = list(map(
            remove_offset_from_julian_date, calculated_metrics.winter_timings[key], itertools.repeat(julian_start_date)))
        winter_timings[value +
                       '_water'] = calculated_metrics.winter_timings[key]
        winter_durations[value] = calculated_metrics.winter_durations[key]
        winter_magnitudes[value] = calculated_metrics.winter_magnitudes[key]
        winter_frequencys[value] = calculated_metrics.winter_frequencys[key]

    result["winter"]["timings"] = winter_timings
    result["winter"]["magnitudes"] = winter_magnitudes
    result["winter"]["durations"] = winter_durations
    result["winter"]["frequencys"] = winter_frequencys
    
    result["fall"] = {}
    # result["fall"]["timings_julian"] = list(map(
    #     remove_offset_from_julian_date, calculated_metrics.fall_timings, itertools.repeat(julian_start_date)))
    result["fall"]["magnitudes"] = calculated_metrics.fall_magnitudes
    result["fall"]["timings_water"] = calculated_metrics.fall_timings
    result["fall"]["durations"] = calculated_metrics.fall_durations
    
    result["summer"] = {}
    result["summer"]["magnitudes_fifty"] = calculated_metrics.summer_50_magnitudes
    result["summer"]["magnitudes_ninety"] = calculated_metrics.summer_90_magnitudes
    result["summer"]["timings_water"] = calculated_metrics.summer_timings
    # result["summer"]["timings_julian"] = list(map(
    #     remove_offset_from_julian_date, calculated_metrics.summer_timings, itertools.repeat(julian_start_date)))
    result["summer"]["durations_wet"] = calculated_metrics.summer_wet_durations
    # result["summer"]["durations_flush"] = calculated_metrics.summer_flush_durations
    result["summer"]["no_flow_counts"] = calculated_metrics.summer_no_flow_counts
    
    result["wlf"] = {}
    result["wlf"]["magnitudes_fifty"] = calculated_metrics.wlf_mag_50
    result["wlf"]["magnitudes_ninety"] = calculated_metrics.wlf_mag_90
    result["wlf"]["durations"] = calculated_metrics.wlf_dur
    
    result["slf"] = {}
    result["slf"]["magnitudes_fifty"] = calculated_metrics.slf_mag_50
    result["slf"]["magnitudes_ninety"] = calculated_metrics.slf_mag_90
    result["slf"]["durations"] = calculated_metrics.slf_dur
    
    result["spring"] = {}
    # result["spring"]["magnitudes"] = calculated_metrics.spring_magnitudes
    # result["spring"]["timings_julian"] = list(map(
    #     remove_offset_from_julian_date, calculated_metrics.spring_timings, itertools.repeat(julian_start_date)))
    result["spring"]["timings_water"] = calculated_metrics.spring_timings
    result["spring"]["durations"] = calculated_metrics.spring_durations
    result["spring"]["rocs"] = calculated_metrics.spring_rocs
    
    result["wet"] = {}
    result["wet"]["baseflows_10"] = calculated_metrics.wet_baseflows_10
    result["wet"]["baseflows_50"] = calculated_metrics.wet_baseflows_50
    # result["fall"]["wet_timings_julian"] = list(map(
    #     remove_offset_from_julian_date, calculated_metrics.fall_wet_timings, itertools.repeat(julian_start_date)))
    result["wet"]["wet_timings_water"] = calculated_metrics.fall_wet_timings
    result["wet"]["bfl_durs"] = calculated_metrics.wet_bfl_durs
    
    result["hfa"] = {}
    result["hfa"]["ROC_daily"] = calculated_metrics.hfa_ROC_daily
    # result["hfa"]["ROC_1090"] = calculated_metrics.hfa_ROC_1090

    return result


def write_to_csv(file_name, result, file_type, *args):
    year_ranges = ",".join(str(year) for year in result['year_ranges'])

    if file_type == 'annual_flow_matrix':

        a = np.array(result['flow_matrix'])
        np.savetxt(file_name + '_' + file_type + '.csv', a, delimiter=',',
                   header=year_ranges, fmt='%s', comments='')

    if file_type == 'drh':
        dataset = []
        for key, value in result['DRH'].items():
            data = value
            data.insert(0, key)
            dataset.append(data)

        a = np.array(dataset)
        np.savetxt(file_name + '_' + file_type +
                   '.csv', a, delimiter=',', fmt='%s', comments='')

    if file_type == 'annual_flow_result':
        # remove summer no_flow, LF_Mag_50, LF_Mag_90, and LF_Dur from main output but save it for supplementary outputs
        summer_no_flow = result['summer']['no_flow_counts']
        lf_mag_50 = result['summer']['magnitudes_fifty']
        lf_mag_90 = result['summer']['magnitudes_ninety']
        lf_dur = result['summer']['durations_wet']
        del result['summer']['no_flow_counts']
        del result['summer']['magnitudes_fifty']
        del result['summer']['magnitudes_ninety']
        del result['summer']['durations_wet']

        dataset = []
        # dict_to_array(result['all_year'], 'all_year', dataset)
        # dict_to_array(result['fall'], 'fall', dataset) # Remove fall metrics from all reporting for now
        dict_to_array(result['wet'], 'wet', dataset)
        dict_to_array(result['winter'], 'winter', dataset)
        dict_to_array(result['hfa'], 'hfa', dataset)
        dict_to_array(result['spring'], 'spring', dataset)
        dict_to_array(result['summer'], 'summer', dataset)
        dict_to_array(result['wlf'], 'wlf', dataset)
        dict_to_array(result['slf'], 'slf', dataset)

        # Change any nan to None for consistency in output file
        for index, ls in enumerate(dataset):
            for i_index, item in enumerate(ls):
                if isinstance(item, str) == False and item is not None:
                    if math.isnan(item):
                        dataset[index][i_index] = None

        a = np.array(dataset)
        np.savetxt(file_name + '_' + file_type + '.csv', a, delimiter=',',
                   fmt='%s', header='Year, ' + year_ranges, comments='')

        """Create supplementary metrics file"""
        supplementary = []
        supplementary.append(['Avg'] + result['all_year']
                             ['average_annual_flows'])
        # supplementary.append(['Std'] + result['all_year']
        #                      ['standard_deviations'])
        # supplementary.append(['CV'] + result['all_year']
        #                      ['coefficient_variations'])
        # supplementary.append(['LF_No_Flow'] + summer_no_flow)
        supplementary.append(['LF_Mag_50'] + lf_mag_50)
        supplementary.append(['LF_Mag_90'] + lf_mag_90)
        supplementary.append(['LF_Dur'] + lf_dur)
        supplementary.append(['Annual_Peak'] + result['all_year']
                             ['annual_peaks'])
        np.savetxt(file_name + '_supplementary_metrics.csv', supplementary, delimiter=',',
                   fmt='%s', header='Year, ' + year_ranges, comments='')

    if file_type == 'parameters':
        now = datetime.now()
        timestamp = now.strftime("%m/%d/%Y, %H:%M")
        flow_class = args

        cols = {'Date_time': timestamp, 'Stream_class': flow_class[0]}
        df = pd.DataFrame(cols, index=[0])
        df['Fall_params'] = '_'
        for key, value in fall_params.items():
            # modify all key names to make sure they are distinct from other dataframe entries (otherwise will not be added)
            key = key + '_fall'
            df[key] = value
        df['Wet_params'] = '_'
        for key, value in winter_params.items():
            key = key + '_wet'
            df[key] = value
        df['Spring_params'] = '_'
        for key, value in spring_params.items():
            key = key + '_spring'
            df[key] = value
        df['Dry_params'] = '_'
        for key, value in summer_params.items():
            key = key + '_dry'
            df[key] = value
        df = df.transpose()
        df.to_csv(file_name + '_' + 'run_metadata.csv', sep=',', header=False)


def dict_to_array(data, field_type, dataset):
    for key, value in data.items():
        if field_type == 'winter':
            for k, v in value.items():
                if key.find('timings') > -1:
                    continue
                data = v
                # remove everything except 2yr recurrence (50th percentile) from output
                if k.find('two') > -1 or k.find('five') > -1 or k.find('ten') > -1 or k.find('twenty') > -1:
                    continue
                else:
                    if k.find('_water') > -1:
                        tmp = k.split('_water')[0]
                        data.insert(
                            0, TYPES[field_type+'_'+key+'_'+str(tmp)] + '_water')
                    else:
                        data.insert(0, TYPES[field_type+'_'+key+'_'+str(k)])
                    dataset.append(data)

        else:
            data = value
            data.insert(0, TYPES[field_type+'_'+key])
            dataset.append(data)

def draw_plots(file_name, results):
    # flow from annual matrix
    flow_matrix = results['flow_matrix']
    flow_matrix = list(map(list, zip(*flow_matrix)))
    x_axis = range(len(flow_matrix[0]))
    # convert x axis to months
    month_ticks = [0,32,60,91,121,152,182,213,244,274,305,335]
    month_labels = ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep']
    # compile timing arrays from results file
    fall_timings = results['fall']['timings_water']
    wet_timings = results['wet']['wet_timings_water']
    spring_timings = results['spring']['timings_water']
    summer_timings = results['summer']['timings_water']

    for index, flow_col in enumerate(flow_matrix):
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(x_axis, flow_col)
        plt.xticks(month_ticks, month_labels)
        ax.set_ylabel('Flow')
        year = results['year_ranges'][index]
        # import pdb; pdb.set_trace()
        # if fall_timings[index+1] is not None:
        #     plt.axvline(fall_timings[index+1], ls=":", c="blue", label="fall pulse")
        if wet_timings[index+1] is not None:
            plt.axvline(wet_timings[index+1], ls=":", c="#00aef0", label="start of high flow")
        if spring_timings[index+1] is not None:
            plt.axvline(spring_timings[index+1], ls=":", c="#01b04d", label="start of recession")
        if summer_timings[index+1] is not None:
            plt.axvline(summer_timings[index+1], ls=":", c="#f84da7", label="start of summer low flow")
        ax.legend()
        plt.title("Gage #{}, WY {}".format(file_name.split("/")[1], year))
        plt.savefig(file_name + '_{}.png'.format(year), bbox_inches='tight')
    return()

def read_csv_to_arrays(file_path):
    fields = ['date', 'flow']

    df = pd.read_csv(file_path, skipinitialspace=True, usecols=fields)

    dates = df['date']
    flow = df['flow']

    return {'date': dates, 'flow': flow}
