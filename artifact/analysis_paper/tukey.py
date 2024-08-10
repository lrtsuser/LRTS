import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import sys
from itertools import combinations
from scipy import stats

args = sys.argv[1:]

def lastC(s):
    return s[-1] if s else ''

def orderPvalueCustom(treatment, means, alpha, pvalue, console):
    n = len(means)
    z = pd.DataFrame({'treatment': treatment, 'means': means})
    letras = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456789.+-*/#$%&^[]:@;_?!=') + [' '] * 2000
    w = z.sort_values('means', ascending=False).reset_index(drop=True)
    M = [''] * n
    k = 0
    j = 0
    cambio = n
    cambio1 = 0
    chequeo = 0
    M[0] = letras[k]
    q = z['means'].argsort()[::-1].tolist()

    while j < n - 1:
        chequeo += 1
        if chequeo > n:
            break

        for i in range(j, n):
            s = pvalue.iloc[q[i], q[j]] > alpha
            if s:
                if lastC(M[i]) != letras[k]:
                    M[i] += letras[k]
            else:
                k += 1
                cambio = i
                cambio1 = 0
                ja = j
                for jj in range(cambio, n):
                    M[jj] += ''
                M[cambio] += letras[k]
                for v in range(ja, cambio + 1):
                    if pvalue.iloc[q[v], q[cambio]] <= alpha:
                        j += 1
                        cambio1 = 1
                    else:
                        break
                break
        if cambio1 == 0:
            j += 1

    w['stat'] = M
    trt = w['treatment'].tolist()
    means = w['means'].tolist()
    output = pd.DataFrame({'score': means, 'groups': M}, index=trt)
    if k > 81:
        print(f"\n{k} groups are estimated. The number of groups exceeded the maximum of 81 labels. Change to group=FALSE.\n")
    return output

def HSDtestCustom(junto, DFerror, MSerror, alpha=0.05, group=True, main=None, unbalanced=False):
    medians = junto.groupby('trt')['y'].agg(['median'] + [lambda x: np.quantile(x, q) for q in [0, 1, 0.25, 0.5, 0.75]])
    medians.columns = ['median', 'Min', 'Max', 'Q25', 'Q50', 'Q75']
    means = junto.groupby('trt')['y'].agg(['mean', 'std', 'count']).rename(columns={'mean': 'score', 'std': 'std', 'count': 'r'})
    means = means.join(medians)
    means = means.reset_index()
    means = means.rename(columns={'trt': 'tcp'})

    ntr = len(means)
    nr1 = 1 / np.mean(1 / means['r'])
    comb = list(combinations(range(ntr), 2))
    nn = len(comb)
    dif = np.zeros(nn)
    pvalue = np.zeros(nn)

    for k, (i, j) in enumerate(comb):
        dif[k] = means.iloc[i]['score'] - means.iloc[j]['score']
        sdtdif = np.sqrt(MSerror * 0.5 * (1 / means.iloc[i]['r'] + 1 / means.iloc[j]['r']))
        if unbalanced:
            sdtdif = np.sqrt(MSerror / nr1)
        pvalue[k] = round(1 - stats.studentized_range.cdf(abs(dif[k]) / sdtdif, ntr, DFerror), 4)

    if group:
        Q = np.ones((ntr, ntr))
        k = 0
        for i in range(ntr - 1):
            for j in range(i + 1, ntr):
                Q[i, j] = pvalue[k]
                Q[j, i] = pvalue[k]
                k += 1
        groups = orderPvalueCustom(means['tcp'], means['score'], alpha, pd.DataFrame(Q), console=True)
    
    return groups

t = pd.read_csv(args[0])
model_lm = smf.ols('score ~ tcp', data=t).fit()
DFerror = model_lm.df_resid
MSerror = model_lm.mse_resid
trtdf = pd.DataFrame()
trtdf["y"] = t["score"]
trtdf["trt"] = t["tcp"]
groups = HSDtestCustom(junto=trtdf, DFerror=DFerror, MSerror=MSerror, alpha=0.05, unbalanced=True)
groups.to_csv(args[1], sep=",", index=True)
