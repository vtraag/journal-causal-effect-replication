import pystan
import pickle
#%%
citation_stan_code = """
functions
{
  real decay_interval(int t1, int t2, real beta)
  {
    return exp(-t1/beta) - exp(-t2/beta);
  }

  real log_decay_interval(int t1, int t2, real beta)
  {
    return log_diff_exp(-t1/beta, -t2/beta);
  }
  
  real decay_lpmf(int t, real beta)
  {
    return log_decay_interval(t, t + 1, beta);
  } 
}
data
{
  int<lower=0> N_art;              // Number of articles
  
  int<lower=0> total_n_T;          // Sum of n_T
  int<lower=0> n_T[N_art];         // Number of time points per article

  int<lower=0> max_T[N_art];       // Maximum time point per article
  int<lower=0> T_published[N_art]; // Time until published per article

  // The following contains N_art arrays, each of length n_T[i]
  int<lower=0> T_cit[total_n_T];   // Time article was cited 
  int<lower=0> cit[total_n_T];     // Number of times article was cited at time T_cit

  real<lower=0> m;
  int print;
}
parameters 
{
  real mu_value_journal;
  real<lower=0> sigma_value_journal;
  
  real<lower=0> theta;
  
  real<lower=0> v_art[N_art];
  
  real<lower=0> beta_decay[N_art];

}
model 
{
  int idx_total = 0;
  int cum_cit;
  int T;
  int prev_T;
  real log_rate;
  real lambda;

  mu_value_journal ~ normal(0, 1);
  sigma_value_journal ~ inv_gamma(2, 1);
  
  theta ~ gamma(3, 3);
  
  for (i in 1:N_art)
  {
    v_art[i] ~ lognormal(mu_value_journal, sigma_value_journal);
 
    beta_decay[i] ~ inv_gamma(2, 3*365);
    
    cum_cit = 0;
    prev_T = -1;
    for (idx in 1:n_T[i])
    {
      T = T_cit[idx_total + idx];
  
      if (T <= T_published[i])
        lambda = v_art[i];
      else
        lambda = v_art[i] * theta;
      
      if (T > prev_T + 1)
      {
          if (T > T_published[i] && prev_T <= T_published[i])
          {
            // Before T_published
            target += -v_art[i] * (m + cum_cit) * decay_interval(prev_T + 1, T_published[i], beta_decay[i]);
            // After T_published
            target += -v_art[i] * theta * (m + cum_cit) * decay_interval(T_published[i], T, beta_decay[i]);
          }
          else
            target += -lambda * (m + cum_cit) * decay_interval(prev_T + 1, T, beta_decay[i]);
      }
      
      log_rate = log(lambda) + log(m + cum_cit) + decay_lpmf(T | beta_decay[i]);

      cit[idx_total + idx] ~ poisson_log(log_rate);
      
      cum_cit += cit[idx_total + idx];
      prev_T = T;
    }
    idx_total += n_T[i];

    T = prev_T; // Necessary in case n_T == 0  

    if (max_T[i] > T + 1)
    {
      if (max_T[i] > T_published[i] && T <= T_published[i])
      {
        // Before T_published
        target += -v_art[i] * (m + cum_cit) * decay_interval(T + 1, T_published[i], beta_decay[i]);
        // After T_published
        target += -v_art[i] * theta * (m + cum_cit) * decay_interval(T_published[i], max_T[i], beta_decay[i]);
      }
      else
      {
        if (T <= T_published[i])
          target += -v_art[i] * (m + cum_cit) * decay_interval(T + 1, max_T[i], beta_decay[i]);
        else
          target += -v_art[i] * theta * (m + cum_cit) * decay_interval(T + 1, max_T[i], beta_decay[i]);
      }
    }
      
  }
}
"""
data_generation_code = """
generated quantities
{
  real<lower=0> pred_cit_pre[N_art];
  real<lower=0> pred_cit_post[N_art];

  real log_theta = log(theta);

  for (i in 1:N_art)
  {
      int cit_sample;
      real cum_cit = 0;
      real log_rate = 0;
      real log_rate_limit = log(pow(2, 30));
      real lambda = 0;
      
      pred_cit_pre[i] = 0;
      pred_cit_post[i] = 0;

      cum_cit = 0;
      for (t in 1:max_T[i])
      {
        if (t <= T_published[i])
          lambda = v_art[i];
        else
          lambda = v_art[i] * theta;
      
        log_rate = log(lambda) + log(m + cum_cit) + decay_lpmf(t - 1 | beta_decay[i]);

        if (log_rate >= log_rate_limit)
        {
          if (t <= T_published[i])
            pred_cit_pre[i] = positive_infinity();
          else
            pred_cit_post[i] = positive_infinity();
          break;
        }

        cit_sample = poisson_log_rng(log_rate);
        if (t <= T_published[i])
          pred_cit_pre[i] += cit_sample;
        else
          pred_cit_post[i] += cit_sample;
          
        cum_cit += cit_sample;
      }
   }
}
"""
sm = pystan.StanModel(model_code=citation_stan_code + data_generation_code)
#%%
# save it to the file 'model.pkl' for later use
with open('cit_model.pkl', 'wb') as f:
    pickle.dump(sm, f)
