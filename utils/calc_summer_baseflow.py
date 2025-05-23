import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
import scipy.interpolate as ip
import math
from scipy.ndimage import gaussian_filter1d
from utils.helpers import find_index, peakdet, replace_nan
from params import summer_params as def_summer_params
from utils.helpers import set_user_params


def calc_start_of_summer(matrix, class_number, summer_params=def_summer_params):
    """Set adjustable parameters for start of summer date detection"""
    params = set_user_params(summer_params, def_summer_params)

    max_zero_allowed_per_year, max_nan_allowed_per_year, sigma, sensitivity, peak_sensitivity, max_peak_flow_date, min_summer_flow_percent, min_flow_rate = params.values()

    start_dates = []
    for column_number, flow_data in enumerate(matrix[0]):
        start_dates.append(None)
        """Check if data has too many zeros or NaN, and if so skip to next water year"""
        if pd.isnull(matrix[:, column_number]).sum() > max_nan_allowed_per_year or np.count_nonzero(matrix[:, column_number] == 0) > max_zero_allowed_per_year or max(matrix[:, column_number]) < min_flow_rate:
            continue

        """Append each column with 15 more days from next column for peak detection, except the last column"""
        if column_number != len(matrix[0])-1:
            flow_data = list(np.copy(matrix[:, column_number])) + \
                list(np.copy(matrix[:15, column_number+1]))
        else:
            flow_data = np.copy(matrix[:, column_number])

        """Replace any NaNs with previous day's flow"""
        flow_data = replace_nan(flow_data)

        """Set specific parameters for rain-dominated classes"""
        if class_number == 4 or class_number == 6 or class_number == 7 or class_number == 8:
            sensitivity = 1100
            peak_sensitivity = .1
            sigma = 4

        """Smooth out the timeseries"""
        smooth_data = gaussian_filter1d(flow_data, sigma)
        x_axis = list(range(len(smooth_data)))

        """Find spline fit equation for smoothed timeseries, and find derivative of spline"""
        spl = ip.UnivariateSpline(x_axis, smooth_data, k=3, s=3)
        spl_first = spl.derivative(1)

        max_flow_data = max(smooth_data[:366])
        max_flow_index = find_index(smooth_data, max_flow_data)

        """Find the major peaks of the filtered data"""
        mean_flow = np.nanmean(flow_data)
        maxarray, minarray = peakdet(smooth_data, mean_flow * peak_sensitivity)
        """Set search range after last smoothed peak flow"""
        for flow_index in reversed(maxarray):
            if int(flow_index[0]) < max_peak_flow_date:
                max_flow_index = int(flow_index[0])
                break

        """Set a magnitude threshold below which start of summer can begin"""
        min_flow_data = min(smooth_data[max_flow_index:366])
        threshold = min_flow_data + \
            (smooth_data[max_flow_index] - min_flow_data) * \
            min_summer_flow_percent

        current_sensitivity = 1/sensitivity
        start_dates[-1] = None
        for index, data in enumerate(smooth_data):
            if index == len(smooth_data)-2:
                break
            """Search criteria: derivative is under rate of change threshold, date is after last major peak, and flow is less than specified percent of smoothed max flow"""
            if abs(spl_first(index)) < max_flow_data * current_sensitivity and index > max_flow_index and data < threshold:
                start_dates[-1] = index
                break

        # _summer_baseflow_plot(x_axis, column_number, flow_data, spl, spl_first, start_dates, threshold, max_flow_index, maxarray)

    return start_dates


def calc_summer_baseflow_durations_magnitude(flow_matrix, summer_start_dates, fall_flush_dates, fall_flush_wet_dates):
    summer_90_magnitudes = []
    summer_50_magnitudes = []
    summer_flush_durations = []
    summer_wet_durations = []
    summer_no_flow_counts = []
    wlf_mag_50 = []
    wlf_mag_90 = []
    wlf_dur = []
    slf_dur = []
    slf_mag_50 = []
    slf_mag_90 = []

    for column_number, summer_start_date in enumerate(summer_start_dates):
        if column_number == len(summer_start_dates) - 1: # calcs for final year on record
            # Final year on record does not include data for portion of low flow period after Sept 30th
            # Do not calculate metrics that depend on the subsequent high flow start date. 
            summer_90_magnitudes.append(None)
            summer_50_magnitudes.append(None)
            summer_flush_durations.append(None)
            summer_wet_durations.append(None)
            summer_no_flow_counts.append(None)
            wlf_mag_50.append(None)
            wlf_mag_90.append(None)
            wlf_dur.append(None)
            slf_dur.append(None)
            slf_mag_50.append(None)
            slf_mag_90.append(None)
            continue
        
        else: # for every year up until last one
            if not pd.isnull(summer_start_date) and not pd.isnull(fall_flush_wet_dates[column_number + 1]):
                su_date = int(summer_start_date)
                wet_date = int(fall_flush_wet_dates[column_number + 1])
                flow_data_flush = None
                if not pd.isnull(fall_flush_dates[column_number + 1]):
                    fl_date = int(fall_flush_dates[column_number + 1])
                    flow_data_flush = list(
                        flow_matrix[su_date:, column_number]) + list(flow_matrix[:fl_date, column_number + 1])
                if not pd.isnull(fall_flush_wet_dates[column_number + 1]):
                    flow_data_wet = list(
                        flow_matrix[su_date:, column_number]) + list(flow_matrix[:wet_date, column_number + 1])

            else:
                flow_data_flush = None
                flow_data_wet = None
            # Utah func flows: add summer duration based on a fixed end date (Oct 15) and winter low flow (after Oct 15)
            if not pd.isnull(summer_start_date):
                su_date = int(summer_start_date)
                flow_data_Oct = list(flow_matrix[su_date:, column_number]) + list(flow_matrix[:15, column_number + 1])
                slf_dur.append(len(flow_data_Oct))
                slf_mag_50.append(np.nanpercentile(flow_data_Oct, 50))
                slf_mag_90.append(np.nanpercentile(flow_data_Oct, 90))

            else:
                slf_dur.append(None)
                slf_mag_50.append(None)
                slf_mag_90.append(None)
            if not pd.isnull(fall_flush_wet_dates[column_number]):
                wet_date = int(fall_flush_wet_dates[column_number])
                flow_data_WLF = list(
                flow_matrix[15:wet_date-1, column_number]) # Start on Oct 16
                wlf_mag_50.append(np.nanpercentile(flow_data_WLF, 50))
                wlf_mag_90.append(np.nanpercentile(flow_data_WLF, 90))
                wlf_dur.append(len(flow_data_WLF))
            else:
                wlf_mag_50.append(None)
                wlf_mag_90.append(None)
                wlf_dur.append(None)

        # check for nan in flow data and remove 
        if flow_data_wet is not None:
            flow_data_wet = [x for x in flow_data_wet if not (isinstance(x, float) and math.isnan(x)) and x is not None]
        if flow_data_flush is not None:
            flow_data_flush = [x for x in flow_data_flush if not (isinstance(x, float) and math.isnan(x)) and x is not None]

        if flow_data_flush and flow_data_wet:
            summer_90_magnitudes.append(np.nanpercentile(flow_data_wet, 90))
            summer_50_magnitudes.append(np.nanpercentile(flow_data_wet, 50))
            summer_flush_durations.append(len(flow_data_flush))
            summer_wet_durations.append(len(flow_data_wet))
            summer_no_flow_counts.append(
                len(flow_data_wet) - np.count_nonzero(flow_data_wet))
        elif not flow_data_flush and flow_data_wet:
            summer_90_magnitudes.append(np.nanpercentile(flow_data_wet, 90))
            summer_50_magnitudes.append(np.nanpercentile(flow_data_wet, 50))
            summer_flush_durations.append(None)
            summer_wet_durations.append(len(flow_data_wet))
            summer_no_flow_counts.append(
                len(flow_data_wet) - np.count_nonzero(flow_data_wet))
        else:
            summer_90_magnitudes.append(None)
            summer_50_magnitudes.append(None)
            summer_flush_durations.append(None)
            summer_wet_durations.append(None)
            summer_no_flow_counts.append(None)

    return summer_90_magnitudes, summer_50_magnitudes, summer_flush_durations, summer_wet_durations, summer_no_flow_counts, \
wlf_mag_50, wlf_mag_90, wlf_dur, slf_mag_50, slf_mag_90, slf_dur


# def _summer_baseflow_plot(x_axis, column_number, flow_data, spl, spl_first, start_dates, threshold, max_flow_index, maxarray):

#     plt.figure(column_number)

#     plt.plot(x_axis, spl_first(x_axis), color='red')  # spl 1st derivative
#     plt.plot(flow_data, '-', color='blue')  # raw
#     plt.plot(x_axis, spl(x_axis), '--', color='orange')  # spline
#     plt.title('Start of Summer Metric')
#     plt.xlabel('Julian Day')
#     plt.ylabel('Flow, ft^3/s')
#     if start_dates[-1] is not None:
#         plt.axvline(start_dates[-1], color='red')
#     plt.axhline(threshold, color='green')
#     plt.axvline(max_flow_index, ls=':')
#     for data in maxarray:
#         plt.plot(data[0], data[1], '^')

#     plt.savefig('post_processedFiles/Boxplots/{}.png'.format(column_number))
