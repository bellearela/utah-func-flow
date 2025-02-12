# convert dates on input files
import pandas as pd
import glob
import os

# navigate to input files
input_fps = glob.glob('user_input_files/*.csv')
# for each file:
for fp in input_fps:
    file = pd.read_csv(fp)
    name = os.path.basename(fp)
    date_col = file['date']
    dttime = pd.to_datetime(date_col)
    file['date'] = dttime.dt.strftime('%m/%d/%Y')
    file.to_csv('user_input_files/interp_processed/{}'.format(name))
import pdb; pdb.set_trace()
# open with pandas
# convert to datetime
# save in new folder