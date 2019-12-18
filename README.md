The material in this repository is meant to replicate the results of [1]. It contains both the necessary data and the source code to replicate our results.

# Data

The data for replication is available from Zenodo, doi: [10.5281/zenodo.3582974](https://dx.doi.org/10.5281/zenodo.3582974). The dataset should be downloaded and extracted to a subdirectory of this repository called `data`. Please see the `README.md` in the data repository for more details regarding the data.

# Source code

All necessary source code is contained in the `src` directory. This code is executed using `python 3.6.6`, `pandas 0.23.4` and `pystan 2.18.0.0`.

The data is processed in subsets, per field and year. We first process the data to separate it into suitable subsets using `prepare_data.py`. We then create the `pystan` model using `cit_stan_create.py`, which is pickled to `cit_model.pkl`. The pickled model is then reused by `cit_stan_run.py`, which runs the `pystan` model on one particular subset. This is explained in more detail below.

1. Prepare the subsets. This should be done by executing the following from the `src` directory.

   ``python prepare_date.py``

   This script assumes all data is contained in the `data` directory, and will create a directory in `data/subsets` for each subset that fulfills the conditions (i.e. at least 20 preprints published no sooner than 30 days after being posted on arXiv). The subsets are organised as `[subject]/[journal]/[year]`.
   Note that it will not recreate a directory if it already exists. If a directory already exists but it shouldn't according to the criteria, it is removed.

2. Create the `pystan` model. This is done by executing the following from the `src` directory.

    ``python cit_stan_create.py``

    This script will create a `cit_model.pkl` file in the current working directory, which contains the pickled `pystan` model. It takes quite a bit of time to compile the model, and we therefore seperately create the model and reuse it on each subset.

3. Run the `pystan` model on each subset. This is done by executing the following

   ``python cit_stan_run.py [source dir] [data subset dir] [result subset dir]``

   The `[source dir]` should refer to the directory in which `cit_model.pkl` is available. If the previous step was simply run from the `src` directory, and this script is also run from the `src` directory, you can simply indicate the current directory (`.`). The `[data subset dir]` should refer to a specific subset for which you wish to run the `pystan` model, e.g. `../data/subsets/Astrophysics/12375/2004`. The `[result subset dir]` should refer to the directory in which you would like the results to be stored, e.g. `../results/subsets/Astrophysics/12375/2004`. If the directory does not yet exist it will be created (including intermediate directories). The result consists of two files: `fit.csv` and `stan_summary.txt`. The first contains the samples from the posterior distributions, and the latter contains a summary of the samples. Note that a [bug](https://github.com/stan-dev/pystan/issues/429) in the summary file in `pystan` may result in incorrectly aligned summary files. Existing files will be overwritten.

   This setup allows to run the `pystan` model on all 3892 different subsets in parallel. For the original results, all calculations were performed on the Shark cluster of the LUMC.

# References

[1] Traag, V.A. (2019), Inferring the causal effect of journals on citations.