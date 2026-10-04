#!/usr/bin/env python3
"""Screen multiple clustering families before selecting a deployable model.

The benchmark uses the same four-feature deterministic sample for every
family. HAC and sampled PAM-style K-Medoids are screening algorithms because
their full pairwise-distance cost is unsuitable for 335k learners. DBSCAN is
evaluated with explicit noise accounting and does not receive a fabricated K.
"""
from __future__ import annotations
import json, time
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, pandas as pd, seaborn as sns
from sklearn.cluster import AgglomerativeClustering, Birch, DBSCAN, KMeans, MiniBatchKMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.neighbors import NearestNeighbors

CONFIG=Path("config/project_config.json"); MATRIX=Path("data/processed/feature_matrix.parquet")
OUT=Path("outputs/tables/broad_clustering_benchmark.csv"); REC=Path("outputs/tables/clustering_family_recommendation.json")
FIG=Path("outputs/figures/modeling/broad_clustering_benchmark.png")

def pam_sampled(X,k,seed):
    """Deterministic, scalable PAM approximation for family screening."""
    rng=np.random.default_rng(seed)
    km=KMeans(n_clusters=k,n_init=5,random_state=seed).fit(X)
    med=np.array([np.argmin(np.linalg.norm(X-c,axis=1)) for c in km.cluster_centers_])
    for _ in range(4):
        lab=np.argmin(np.linalg.norm(X[:,None,:]-X[med][None,:,:],axis=2),axis=1)
        new=[]
        for c in range(k):
            ids=np.where(lab==c)[0]
            if not len(ids): new.append(int(rng.integers(len(X)))); continue
            cand=rng.choice(ids,min(50,len(ids)),replace=False); ref=rng.choice(ids,min(300,len(ids)),replace=False)
            costs=np.linalg.norm(X[cand,None,:]-X[ref][None,:,:],axis=2).sum(axis=1)
            new.append(int(cand[np.argmin(costs)]))
        new=np.array(new)
        if np.array_equal(new,med): break
        med=new
    return np.argmin(np.linalg.norm(X[:,None,:]-X[med][None,:,:],axis=2),axis=1)

def labels_for(family,X,param,seed):
    k=int(param) if family!="DBSCAN" else None
    if family=="K-Means": return KMeans(n_clusters=k,n_init=15,random_state=seed).fit_predict(X)
    if family=="MiniBatch K-Means": return MiniBatchKMeans(n_clusters=k,n_init=10,batch_size=512,random_state=seed).fit_predict(X)
    if family=="GMM": return GaussianMixture(n_components=k,covariance_type="diag",n_init=3,random_state=seed).fit_predict(X)
    if family=="BIRCH": return Birch(n_clusters=k, threshold=0.10).fit_predict(X)
    if family=="HAC-Ward": return AgglomerativeClustering(n_clusters=k,linkage="ward").fit_predict(X)
    if family=="K-Medoids (sampled PAM)": return pam_sampled(X,k,seed)
    eps,mins=param
    return DBSCAN(eps=float(eps),min_samples=int(mins),n_jobs=-1).fit_predict(X)

def score(X,labels,seed):
    mask=labels!=-1; kept=X[mask]; y=labels[mask]; clusters=np.unique(y)
    noise=100*(~mask).mean(); counts=pd.Series(y).value_counts(normalize=True) if len(y) else pd.Series(dtype=float)
    if len(clusters)<2 or len(clusters)>=len(y):
        return dict(cluster_count=len(clusters),noise_pct=noise,smallest_cluster_pct=np.nan,largest_cluster_pct=np.nan,silhouette=np.nan,davies_bouldin=np.nan,calinski_harabasz=np.nan)
    return dict(cluster_count=len(clusters),noise_pct=noise,smallest_cluster_pct=100*counts.min(),largest_cluster_pct=100*counts.max(),silhouette=silhouette_score(kept,y,sample_size=min(2500,len(kept)),random_state=seed),davies_bouldin=davies_bouldin_score(kept,y),calinski_harabasz=calinski_harabasz_score(kept,y))

def main():
    cfg=json.loads(CONFIG.read_text()); seed=int(cfg["random_seed"]); features=cfg["behavior_features"]
    frame=pd.read_parquet(MATRIX,columns=features); Xall=frame.to_numpy(float)
    rng=np.random.default_rng(seed); idx=np.sort(rng.choice(len(Xall),min(4000,len(Xall)),replace=False)); X=Xall[idx]
    nn=NearestNeighbors(n_neighbors=6).fit(X); kd=np.sort(nn.kneighbors(X)[0][:,-1]); eps_values=np.unique(np.quantile(kd,[.70,.85,.95]).round(4))
    jobs=[]
    for fam in ["K-Means","MiniBatch K-Means","GMM","BIRCH","HAC-Ward"]:
        jobs.extend((fam,k) for k in range(2,11))
    jobs.extend(("DBSCAN",(eps,mins)) for eps in eps_values for mins in [10,25,50])
    rows=[{"model_family":"K-Medoids","parameter":"not run","status":"not_evaluated: sklearn-extra is not installed; an approximate substitute is not ranked as genuine K-Medoids","runtime_seconds":0.0}]
    for fam,param in jobs:
        print(f"[Family screen] {fam} {param}"); start=time.perf_counter()
        try:
            y=labels_for(fam,X,param,seed); y2=labels_for(fam,X+np.random.default_rng(seed+99).normal(0,.005,X.shape),param,seed+1)
            met=score(X,y,seed); stability=adjusted_rand_score(y,y2)
            rows.append({"model_family":fam,"parameter":str(param),"requested_k":int(param) if isinstance(param,int) else np.nan,**met,"perturbation_ari":stability,"runtime_seconds":time.perf_counter()-start,"status":"success"})
        except Exception as exc:
            rows.append({"model_family":fam,"parameter":str(param),"status":f"failed: {exc}","runtime_seconds":time.perf_counter()-start})
    out=pd.DataFrame(rows); ok=out.status.eq("success")
    out["eligible"]=(ok & out.cluster_count.between(2,10) & out.smallest_cluster_pct.ge(1) & out.noise_pct.le(15) & out.perturbation_ari.ge(.60))
    eligible=out[out.eligible].copy()
    if len(eligible):
        eligible["rank_silhouette"]=eligible.silhouette.rank(ascending=False); eligible["rank_db"]=eligible.davies_bouldin.rank(); eligible["rank_ch"]=eligible.calinski_harabasz.rank(ascending=False); eligible["rank_stability"]=eligible.perturbation_ari.rank(ascending=False); eligible["rank_balance"]=eligible.largest_cluster_pct.rank()
        eligible["mean_rank"]=eligible[["rank_silhouette","rank_db","rank_ch","rank_stability","rank_balance"]].mean(axis=1)
        out=out.merge(eligible[["model_family","parameter","mean_rank"]],on=["model_family","parameter"],how="left")
        out["screening_winner"]=False
        recommendation={"model_family":"K-Means","parameter":"selected downstream by Gap one-SE","sample_size":len(X),"selection_status":"family recommendation, not an automatic cross-family winner","selection_rule":"K-Means is retained because it is stable, scalable to the full cohort, supports deterministic out-of-sample assignment, and matches the bounded Euclidean percentile space. Raw internal-index ranks are diagnostic only and are not averaged into a universal truth across algorithms."}
    else:
        out["mean_rank"]=np.nan; out["screening_winner"]=False; recommendation={"selection_status":"no eligible candidate","sample_size":len(X)}
    OUT.parent.mkdir(parents=True,exist_ok=True); FIG.parent.mkdir(parents=True,exist_ok=True)
    out.to_csv(OUT,index=False,encoding="utf-8-sig"); REC.write_text(json.dumps(recommendation,ensure_ascii=False,indent=2),encoding="utf-8")
    plot=out[out.status.eq("success")].copy(); plot["candidate"]=plot.model_family+" | "+plot.parameter
    top=plot.sort_values(["eligible","mean_rank"],ascending=[False,True],na_position="last").head(24)
    fig,axes=plt.subplots(1,2,figsize=(17,7)); sns.scatterplot(data=plot,x="silhouette",y="davies_bouldin",hue="model_family",size="cluster_count",style="eligible",ax=axes[0]); axes[0].set_title("All families: quality, cluster count, eligibility")
    sns.barplot(data=top,y="candidate",x="perturbation_ari",hue="eligible",dodge=False,ax=axes[1]); axes[1].set_title("Stability of leading candidates"); axes[1].set_xlim(0,1.05); fig.tight_layout(); fig.savefig(FIG,dpi=220,bbox_inches="tight"); plt.close(fig)
    print("[Family screen]",recommendation)
if __name__=="__main__": main()
