import os
import sys
import pandas as pd

#%%
data_dir = os.path.join('..', 'data')
data_dir_subsets = os.path.join(data_dir, 'subsets')

#%%
# Read citation dynamics
citation_dynamics_df = pd.read_csv(os.path.join(data_dir, 'arxiv_dynamics.csv'),
                                   sep=',', parse_dates=['date'],
                                   dtype={'arxiv_id': str});

citation_dynamics_df = citation_dynamics_df[pd.notnull(citation_dynamics_df['date']) &
                                            pd.notnull(citation_dynamics_df['cit_day'])]
citation_dynamics_df['arxiv_id'] = citation_dynamics_df['arxiv_id'].str.lower()
citation_dynamics_df = citation_dynamics_df.set_index(['arxiv_id', 'doi', 'date'])
citation_dynamics_df = citation_dynamics_df.sort_index()
#%%
# Read link between arxiv and doi and meta data
arxiv_doi_df = pd.read_csv(os.path.join(data_dir, 'arxiv_doi_cits.csv'), sep=',',
                           parse_dates=['preprint_date', 'publication_date'],
                           dtype={'arxiv_id': str});

arxiv_doi_df['arxiv_id'] = arxiv_doi_df['arxiv_id'].str.lower()
#%%
arxiv_doi_df['doi'] = arxiv_doi_df['doi'].str.lower()
arxiv_doi_df['preprint_days'] = arxiv_doi_df['preprint_days'].astype(int)
arxiv_doi_df = arxiv_doi_df[(arxiv_doi_df['preprint_days'] >= 30)]
arxiv_doi_df = arxiv_doi_df.set_index(['arxiv_id', 'doi'])
arxiv_doi_df = arxiv_doi_df.sort_index()

#%%
# Read arxiv classification
arxiv_classification_df = pd.read_csv(os.path.join(data_dir, 'arxiv_classification.csv'), sep=',',
                                      dtype={'arxiv_id': str})

#%% Join on classification
arxiv_doi_classification_df = pd.merge(arxiv_doi_df.reset_index(), arxiv_classification_df,
                                       left_on=['arxiv_id'], right_on=['arxiv_id'])

arxiv_doi_classification_df['pub_year'] = arxiv_doi_classification_df['publication_date'].dt.year
#%%
year_range = (2000, 2016)
#%%
for (subject, journal, pub_year), pubs_df in arxiv_doi_classification_df.groupby(['major_subject', 'srcid', 'pub_year']):
  # Only consider journals that have at least 20 publications in a certain subject.
    print('Considering subject {0}, journal {1}, year {2}'.format(subject, journal, pub_year))
    print('It contains {0} articles for analysis'.format(pubs_df.shape[0]))
    sys.stdout.flush()

    #%%
    results_dir = os.path.join(data_dir_subsets, subject.replace(' ', '-'), str(journal), str(pub_year))
  
    should_prepare_data = pubs_df.shape[0] >= 20 and pub_year >= year_range[0] and pub_year <= year_range[1]
    if not os.path.exists(results_dir):
      if should_prepare_data:
        os.makedirs(results_dir)
  
        #%%
        pubs_df = pubs_df.sort_values('arxiv_id')
        cit_df = citation_dynamics_df.loc[pubs_df['arxiv_id'],:]
        #%%
        filename = os.path.join(results_dir, 'citations.csv')
        print('Writing citations to {0}.'.format(filename))
        sys.stdout.flush()
  
        cit_df.to_csv(filename)
  
        #%%
        filename = os.path.join(results_dir, 'articles.csv')
        print('Writing articles to {0}.\n'.format(filename))
        sys.stdout.flush()
  
        pubs_df.to_csv(filename, index=False)
    #%%
    else:
      if should_prepare_data:
        print('Directory {0} already exists.'.format(results_dir))
      else:
        print('Directory {0} exists, but should not, removing.'.format(results_dir))        
        import shutil
        shutil.rmtree(results_dir)
