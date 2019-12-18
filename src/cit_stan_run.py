import pickle
import os
import sys
import pandas as pd
import datetime as dt
#%%
source_dir = os.path.abspath(sys.argv[1])
print('Using source dir {0}'.format(source_dir))
data_dir = os.path.abspath(sys.argv[2])
print('Using data dir {0}'.format(data_dir))
results_dir = os.path.abspath(sys.argv[3])
print('Using results dir {0}'.format(results_dir))
seed = (int(data_dir.split(os.sep)[-1]) + int(data_dir.split(os.sep)[-2]) + 2) % (2**31 - 1)
print('Using seed {0} for RNG.'.format(seed))
#%%
# load the model from file 'model.pkl'
with open(os.path.join(source_dir, 'cit_model.pkl'), 'rb') as f:
    sm = pickle.load(f)

#%%
max_pub_date = pd.datetime(2018, 1, 1)

#%%
pubs_df = pd.read_csv(os.path.join(data_dir, 'articles.csv'),
                      parse_dates=['preprint_date', 'publication_date'],
                      dtype={'arxiv_id': str})
pubs_df['arxiv_id'] = pubs_df['arxiv_id'].str.lower()
cit_df = pd.read_csv(os.path.join(data_dir, 'citations.csv'),
                     parse_dates=['date'],
                     dtype={'arxiv_id': str})
cit_df['arxiv_id'] = cit_df['arxiv_id'].str.lower()
cit_df = cit_df.set_index('arxiv_id', 'date')

#%% Now concatenate and pass to stan
N = pubs_df.shape[0]

n_T = pd.DataFrame({'n_T': cit_df.groupby(level='arxiv_id').size()})
n_T = pd.merge(n_T, pubs_df[['arxiv_id']], how='outer', right_on='arxiv_id', left_index=True)
n_T = n_T.set_index('arxiv_id')
n_T = n_T.sort_index()
n_T = n_T.fillna(0)
n_T['n_T'] = n_T['n_T'].astype(int)

#%%
print('Processing {0} articles.'.format(N))
print('total citation length: {0}'.format(sum(n_T['n_T'])))
#%%
m = 30
stan_dat = {'N_art': N,
           
           'total_n_T': cit_df.shape[0],
           
           'n_T': n_T['n_T'],
           'max_T': (max_pub_date - pubs_df['preprint_date']).dt.days,
           'T_published': pubs_df['preprint_days'],
           'T_cit': cit_df['cit_day'].astype(int),
           'cit': cit_df['cit'].astype(int),
           
           'm': m,
           'print': 0}
#%%
print('{}: Sampling with pystan'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
fit = sm.sampling(data=stan_dat, iter=1000, chains=4,
                  control={'adapt_delta': 0.98, 'max_treedepth': 20},
                  seed=seed)
#%%
if not os.path.exists(results_dir):
  print('Creating directory {0}'.format(results_dir))
  os.makedirs(results_dir)
#%%
filename = os.path.join(results_dir, 'stan_summary.txt')
print('{}: Writing summary to {}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), filename))
with open(filename, 'w') as f:
  f.write(fit.stansummary())
#%%
filename = os.path.join(results_dir, 'fit.csv')
print('{}: Writing samples to {}'.format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), filename))
fit_df = fit.to_dataframe()
fit_df.to_csv(filename, index=False)
