from helper import *

seed_value= 42
os.environ['PYTHONHASHSEED']=str(seed_value)
random.seed(seed_value)
np.random.seed(seed_value)
import warnings 
warnings.filterwarnings("ignore")
from sklearn.model_selection import permutation_test_score

def run_estimator(cv_outer,output_path,model,X_df,y,text,options,
                    imputer='KNN',neighbors=1,roc_flag='False',fixed_feat=0,rho=1,direction='forward'):
    fmri_feat_outer=['Ov']
    # fmri_feat=['Neg','Pos','Ov']
    fmri_feat=['Ov']
    l,j=2,2
    results,roc_data,y_info,x_feats,grid_search=pd.DataFrame(),pd.DataFrame(),pd.DataFrame(),pd.DataFrame(),pd.DataFrame()
    print('Model:',model,', Imputer:',imputer,', Neighbors:',neighbors)

    for key_2 in fmri_feat_outer:
        l+=1
        # if j>3:
        #     break
        print(key_2,'fmri strength outer')

        for key in fmri_feat:
            j+=1
            print(key,'fmri strength inner')

            # Varying no. of features
            # for i in tqdm(range(2)):
            # for i in tqdm([0.15,0.3,0.5,0.7,0.85,1]):

            for i in tqdm([3]):
                f1_scores,sensitivity1,specificity1,tprs,aucs,feat_sel,p_value = [],[],[],[],[],[],[]
                # y_pred_all,y_test_all=[],[]
                fig, ax = plt.subplots()
                mean_fpr = np.linspace(0, 1, 100)

		        # Start measuring time
                start_time = time.time()

                for k, (train_idx,test_idx) in tqdm(enumerate(cv_outer.split(X_df,y))):
                    
                    y_train = y[train_idx]
                    y_test = y[test_idx]
                    X_train_raw = X_df[train_idx]
                    X_test_raw = X_df[test_idx]
                    
                    if model=='NBF':
                        processed_data_path="../_data"
                        x_d,x_e,x_fn,x_fp,x_fo,y=load_data(processed_data_path,NBF=True)

                        X_train_dwi,y_train_dwi=drop_nan_index(x_d,y,train_idx)
                        X_train_eeg,y_train_eeg=drop_nan_index(x_e,y,train_idx)
                        X_test_dwi=x_d[test_idx,:]
                        X_test_eeg=x_e[test_idx,:]

                        if j==1:
                            X_train_fmri,y_train_fmri=drop_nan_index(x_fn,y,train_idx)
                            X_test_fmri=x_fn[test_idx,:]
                        elif j==2:
                            X_train_fmri,y_train_fmri=drop_nan_index(x_fp,y,train_idx)
                            X_test_fmri=x_fp[test_idx,:]
                        else:
                            X_train_fmri,y_train_fmri=drop_nan_index(x_fo,y,train_idx)
                            X_test_fmri=x_fo[test_idx,:]

                        # SVM Classifiers
                        # fmri_class=nb_svm(X_train_fmri,y_train_fmri)
                        # dwi_class=nb_svm(X_train_dwi,y_train_dwi)
                        # eeg_class=nb_svm(X_train_eeg,y_train_eeg)
                        fmri_class=nb_tree(X_train_fmri,y_train_fmri)
                        dwi_class=nb_tree(X_train_dwi,y_train_dwi)
                        eeg_class=nb_tree(X_train_eeg,y_train_eeg)

                        # feat_sel.append(dwi_class.best_estimator_.named_steps['clf']['kbest'].get_support())
                        # feat_sel.append(eeg_class.best_estimator_.named_steps['clf']['kbest'].get_support())
                        # feat_sel.append(fmri_class.best_estimator_.named_steps['clf']['kbest'].get_support())

                        # np.savetxt(f'{output_path}_feats/{text}_{str(k)}_dmri.txt',x_d[:,dwi_class.best_estimator_.named_steps['clf']['kbest'].get_support()], fmt='%f')
                        # np.savetxt(f'{output_path}_feats/{text}_{str(k)}_fmri.txt',x_fo[:,fmri_class.best_estimator_.named_steps['clf']['kbest'].get_support()], fmt='%f')

                        # print(dwi_class.best_estimator_.named_steps['clf']['kbest'].get_support())
                        # print(eeg_class.best_estimator_.named_steps['clf']['kbest'].get_support())
                        # print(fmri_class.best_estimator_.named_steps['clf'].get_support())

                        dwi_grid = pd.DataFrame(dwi_class.cv_results_)
                        eeg_grid = pd.DataFrame(eeg_class.cv_results_)
                        fmri_grid = pd.DataFrame(fmri_class.cv_results_)
                        grid_search=grid_search.append(dwi_grid)
                        grid_search=grid_search.append(eeg_grid)
                        grid_search=grid_search.append(fmri_grid)

                        y_pred,y_proba,y_prob_false=naive_bayes_multimodal(fmri_class,X_test_fmri,dwi_class,X_test_dwi,y_test,y_train,eeg_class,X_test_eeg)
                        roc_auc=roc_auc_score(y_test, y_proba)

                        # score, permutation_scores, pvalue = permutation_test_score(naive_bayes_multimodal, X_train, y_train, random_state=seed_value)

                    else:
                        # Imputing the train and test splits
                        X_train,X_test=impute_data(imputer,X_train_raw,X_test_raw,fmri_key=j, neighbors=neighbors)
                        X_train_2,X_test_2=impute_data(imputer,X_train_raw,X_test_raw,fmri_key=l, neighbors=neighbors)

                        # Fit and test with desired classifier
                        y_pred,fpr,tpr,roc_auc,X_test_model,pvalue=model_run(model,i,k,ax,X_train,X_test,X_train_2,X_test_2,y_train,y_test,roc_flag,direction,fixed_feat,rho)
                        # Collect p-values from different cv folds
                        p_value.append(pvalue)
                        # y_pred,fpr,tpr,roc_auc,X_test_model,y_proba=model_run(model,i,k,ax,X_train,X_test,X_train_2,X_test_2,y_train,y_test,roc_flag,direction,fixed_feat)
                        
                        # np.savetxt(f'{text}_{str(k)}.txt',X_test_model, fmt='%f')
                        # for m in range(len(y_pred)):
                        #     x_feats=x_feats.append({'X_test_model':X_test_model[m]},ignore_index=True)
                            # y_info=y_info.append({'y_test':y_test[m]*1,'y_pred':y_pred[m]*1,
                            # 'y_proba':y_proba[m,1]},ignore_index=True)                            
                        if options=='X_test':
                            if k==0 and options=='X_test':
                                X_model=np.array(X_test_model)
                                y_model=np.array(y_test)
                            else:                          
                                X_test_model=np.array(X_test_model)
                                y_test=np.array(y_test)
                                X_model=np.append(X_model,X_test_model,axis=0)   
                                y_model=np.append(y_model,y_test,axis=0) 

                    y_test=np.array(y_test)
                    cm1 = confusion_matrix(y_test,y_pred)
                    # cm1 = confusion_matrix(y_test,y_proba)
                    # total1 = sum(sum(cm1))

                    sensitivity1.append(cm1[0,0]/(cm1[0,0]+cm1[0,1]))        
                    specificity1.append(cm1[1,1]/(cm1[1,0]+cm1[1,1]))   
                    f1_scores.append(f1_score(y_test, y_pred, average='weighted'))
                    aucs.append(roc_auc)
                    if roc_flag=='True':
                        interp_tpr = np.interp(mean_fpr,fpr,tpr)
                        interp_tpr[0] = 0.0
                        tprs.append(interp_tpr)

                # End measuring time
                end_time = time.time()
                
                # Print the time complexity
                print(f'Time complexity: ', end_time-start_time)

                if options=='X_test':
                    # X_model=np.array(X_test_model)    
                    # y_model=np.array(y_model)  
                    print(X_model.shape)
                    print(y_model.shape)
                    plot_manifold(output_path,model,X_model,y_model,text,options,imputer,neighbors,fixed_feat)               

                # Record all results 
                # results = results.append({'fMRI_out':key_2,'fMRI_in':key,'Feats_fix':fixed_feat,
                # 'Feats_var':i+1,'rho':rho,'AUC: Mean':round(mean(aucs),3),'AUC: SEM ':round(1.96*stats.sem(aucs,ddof=0),3),
                # 'f1: Mean':round(mean(f1_scores),3),'f1: SEM ':round(1.96*stats.sem(f1_scores,ddof=0),3),'p-value':round(mean(p_value),3)},ignore_index=True)

                # 'Sensitivity':round(mean(sensitivity1),3),
                # 'Specificity':round(mean(specificity1),3)},ignore_index=True)
                # ,'f1: Mean':round(mean(f1_scores),3),'SEM f1':round(1.96*stats.sem(f1_scores,ddof=0),3)

                # np.savetxt(f'{output_path}/_stat/{text}_feat_sel.txt',feat_sel, fmt='%s')
                # grid_search.to_csv(f'{output_path}_stat/{text}_grid_nbf_adb_stat.csv')
                # with open(f'{output_path}_stat/feat_sel.txt', 'w') as filehandle:
                #     json.dump(list(feat_sel), filehandle)

                if roc_flag=='False':
                    plt.close()

    if roc_flag=='True':
        ax.plot([0, 1], [0, 1], linestyle="--", lw=2, color="r", label="Chance", alpha=0.8)

        mean_tpr = np.mean(tprs, axis=0)
        mean_tpr[-1] = 1.0
        mean_auc = auc(mean_fpr, mean_tpr)
        std_auc = np.std(aucs)
        ax.plot(
            mean_fpr,
            mean_tpr,
            color="b",
            label=r"Mean ROC (AUC = %0.2f $\pm$ %0.2f)" % (mean_auc, std_auc),
            lw=2,
            alpha=0.8,
        )

        # Export roc data points to csv
        if options=='roc_data':
            for m in range(mean_fpr.size):
                roc_data = roc_data.append({'mean_fpr':mean_fpr[m],'mean_tpr':mean_tpr[m]},ignore_index=True)
            # x_feats.to_csv(output_path+'extra/'+model+'_'+key+'_'+imputer+'_'+str(neighbors)+'_fixed_'+str(fixed_feat)+text+'_x_feats.csv',index=False)
            roc_data.to_csv(output_path+'extra/'+model+'_'+key+'_'+imputer+'_'+str(neighbors)+'_fixed_'+str(fixed_feat)+text+'_roc_pts.csv')

        elif options=='y_info':
            y_info.to_csv(output_path+'extra/'+model+'_'+key+'_'+imputer+'_'+str(neighbors)+'_fixed_'+str(fixed_feat)+text+'_y_info.csv',index=False)
            # ,header=None


        # Using Binomial conf intervals, as laid out in Sourati 2015
        [tprs_upper, tprs_lower] = binom_conf_interval(mean_tpr*48, 48, confidence_level=0.95, interval='wilson')  

        ax.fill_between(
            mean_fpr,
            tprs_lower,
            tprs_upper,
            color="grey",
            alpha=0.2,
            # label=r"$\pm$ 1 std. dev.",            
            label=r'95% level of confidence',
        )

        ax.set(
            xlim=[-0.05, 1.05],
            ylim=[-0.05, 1.05],
            # title="Receiver operating characteristic example",
        )
        ax.legend(loc="lower right")
        plt.xlabel('1 - Specificity')
        plt.ylabel('Sensitivity')
        plt.savefig(output_path+'_plot/'+model+'_'+key+'_'+imputer+'_'+str(neighbors)+'_fixed_'+str(fixed_feat)+text+'.png') 
    
    # Export all results to csv
    # results.to_csv(output_path+'_stat/'+model+'_'+key+'_'+str(rho)+'_fixed_'+str(fixed_feat)+text+'.csv')

def model_run(model,i,k,ax,X_train_imputed,X_test_imputed,X_train_2,X_test_2,
                y_train,y_test,roc_flag,direction,fixed_feat,rho=1):
    # SVM Classifier
    clf=None
    # clf=make_pipeline(StandardScaler(), SVC(gamma='scale',probability=True))
    clf=make_pipeline(StandardScaler(), AdaBoostClassifier(n_estimators=50))
    # clf=make_pipeline(StandardScaler(), SVC(gamma='auto'))

    if model=='SFS':
        sfs=None
        sfs=SequentialFeatureSelector(clf, direction=direction, scoring='roc_auc', n_features_to_select=i+1)
        X_train=sfs.fit_transform(X_train_imputed,y_train)
        X_test=sfs.transform(X_test_imputed)

        # # removing features above a certain mutual correlation coefficient
        keep_col=[]
        for j in range(X_train.shape[1]):
            keep_col.append(j)
            if j==0:
                continue
            else:
                for m in range(j):
                    r_coef=pearsonr(X_train[:,m],X_train[:,j])[0]
                    if r_coef>=rho:
                        keep_col.remove(j)
                        break

        # Number of selected features (not really "parameters" but relevant for model complexity)
        selected_features_count = sfs.get_support().sum()

        # print("Number of Selected Features:", selected_features_count+1)

        X_train=X_train[:,keep_col]
        X_test=X_test[:,keep_col]
        print('feat=',fixed_feat,'keep_col=',len(keep_col))

    elif model=='SMIG':
        smig=None
        smig=MMINet(input_dim=232, output_dim=i+1, net='linear')
        smig.learn(X_train_imputed, y_train, num_epochs=10)
        X_train_smig = smig.reduce(X_train_imputed)
        X_test_smig = smig.reduce(X_test_imputed)

        # removing features above a certain mutual correlation coefficient
        keep_col=[]
        for j in range(X_train_smig.shape[1]):
            keep_col.append(j)
            if j==0:
                continue
            else:
                for m in range(j):
                    r_coef=pearsonr(X_train_smig[:,m],X_train_smig[:,j])[0]
                    if r_coef>=i:
                        keep_col.remove(j)
                        break

        X_train=X_train_smig[:,keep_col]
        X_test=X_test_smig[:,keep_col]
        print('feat=',fixed_feat,'keep_col=',len(keep_col))

    elif model=='CCA':
        cca=None
        cca=CCA(n_components=i+1)

        # # Get estimator parameters
        # params = cca.get_params()
        # # Count the number of parameters
        # total_parameters = len(params)
        X_train_f,X_train_d=cca.fit_transform(X_train_imputed[:,0:166],X_train_imputed[:,166:229])
        # print(cca.coefs_)
        # print(sum(p.numel() for p in cca.parameters()))
        X_train=np.concatenate((X_train_f,X_train_d), axis=1)
        X_test_f,X_test_d=cca.transform(X_test_imputed[:,0:166],X_test_imputed[:,166:229])
        # X_test_f,X_test_d=cca.transform(X_test_imputed[:,229:232],X_test_imputed[:,0:166])
        X_test=np.concatenate((X_test_f,X_test_d), axis=1)

        # Get the number of features from your dataset for each variable set
        n_features_X = X_train_imputed[:,0:166].shape[1]  # Assuming X is your first variable set
        n_features_Y = X_train_imputed[:,166:229].shape[1]  # Assuming Y is your second variable set

        # Calculate total number of parameters in CCA
        total_parameters = 2 * (n_features_X + n_features_Y) * cca.n_components

        # print(sum(p.numel() for p in scaler.parameters()))
        print('\n cca_parameters: ',total_parameters)

    elif model=='GCCA':
        gcca=None
        gcca=GCCA(latent_dims=i+1)
        # gcca.fit(X_train_imputed[:,0:166],X_train_imputed[:,166:229],X_train_imputed[:,229:232])
        X_train_f,X_train_d,X_train_e=gcca.fit_transform((X_train_imputed[:,0:166],X_train_imputed[:,166:229],X_train_imputed[:,229:232]))
        X_train=np.concatenate((X_train_f,X_train_d), axis=1)
        X_train=np.concatenate((X_train,X_train_e), axis=1)
        X_test_f,X_test_d,X_test_e=gcca.transform((X_test_imputed[:,0:166],X_test_imputed[:,166:229],X_test_imputed[:,229:232]))
        X_test=np.concatenate((X_test_f,X_test_d), axis=1)
        X_test=np.concatenate((X_test,X_test_e), axis=1)      

        # Get the number of features from your dataset for each variable set
        n_features_X = X_train_d.shape[1]  # Assuming X is your first variable set
        n_features_Y = X_train_f.shape[1]  # Assuming Y is your second variable set
        n_features_Z=X_train_e.shape[1]  # Assuming Y is your second variable set

        # Calculate total number of parameters in CCA
        total_parameters = 3 * (n_features_X+n_features_Y+n_features_Z) * gcca.latent_dims

        # print(sum(p.numel() for p in scaler.parameters()))
        print('\n gcca_parameters: ',total_parameters)

    elif model=='GCCA+SMIG':
        # Fix feats in one model, sweep feats in other
        gcca=None
        gcca=GCCA(latent_dims=fixed_feat)
        X_train_f,X_train_d,X_train_e=gcca.fit_transform((X_train_2[:,0:166],X_train_2[:,166:229],X_train_2[:,229:232]))
        X_train_gcca=np.concatenate((X_train_f,X_train_d), axis=1)
        X_train_gcca=np.concatenate((X_train_gcca,X_train_e), axis=1)
        X_test_f,X_test_d,X_test_e=gcca.transform((X_test_2[:,0:166],X_test_2[:,166:229],X_test_2[:,229:232]))
        X_test_gcca=np.concatenate((X_test_f,X_test_d), axis=1)
        X_test_gcca=np.concatenate((X_test_gcca,X_test_e), axis=1)

        smig=None
        smig=MMINet(input_dim=232, output_dim=i+1, net='linear')
        smig.learn(X_train_imputed, y_train, num_epochs=10)
        X_train_smig = smig.reduce(X_train_imputed)
        X_test_smig = smig.reduce(X_test_imputed)

        # removing features above a certain mutual correlation coefficient
        keep_col=[]
        for j in range(X_train_smig.shape[1]):
            keep_col.append(j)
            if j==0:
                continue
            else:
                for m in range(j):
                    r_coef=pearsonr(X_train_smig[:,m],X_train_smig[:,j])[0]
                    if r_coef>=0.5:
                        keep_col.remove(j)
                        break

        X_train_smig=X_train_smig[:,keep_col]
        X_test_smig=X_test_smig[:,keep_col]
        print('feat=',i+1,'keep_col=',len(keep_col))

        X_train=np.concatenate((X_train_gcca,X_train_smig), axis=1)
        X_test=np.concatenate((X_test_gcca,X_test_smig), axis=1)

    elif model=='GCCA+SFS':
        # Fix feats in one model, sweep feats in other
        gcca=None
        gcca=GCCA(latent_dims=fixed_feat)
        X_train_f,X_train_d,X_train_e=gcca.fit_transform((X_train_2[:,0:166],X_train_2[:,166:229],X_train_2[:,229:232]))
        X_train_gcca=np.concatenate((X_train_f,X_train_d), axis=1)
        X_train_gcca=np.concatenate((X_train_gcca,X_train_e), axis=1)
        X_test_f,X_test_d,X_test_e=gcca.transform((X_test_2[:,0:166],X_test_2[:,166:229],X_test_2[:,229:232]))
        X_test_gcca=np.concatenate((X_test_f,X_test_d), axis=1)
        X_test_gcca=np.concatenate((X_test_gcca,X_test_e), axis=1)

        # Get the number of features from your dataset for each variable set
        n_features_X = X_train_2[:,166:229].shape[1]  # Assuming X is your first variable set
        n_features_Y = X_train_2[:,0:166].shape[1]  # Assuming Y is your second variable set
        n_features_Z=X_train_2[:,229:232].shape[1]  # Assuming Y is your second variable set

        # Calculate total number of parameters in CCA
        total_parameters = 3 * (n_features_X+n_features_Y+n_features_Z) * gcca.latent_dims

        # print(sum(p.numel() for p in scaler.parameters()))
        print('\n gcca_parameters: ',total_parameters)

        sfs=None
        sfs=SequentialFeatureSelector(clf, direction=direction, scoring='roc_auc', n_features_to_select=i+1)
        X_train_sfs=sfs.fit_transform(X_train_imputed,y_train)
        X_test_sfs=sfs.transform(X_test_imputed)

        # removing features above a certain mutual correlation coefficient
        keep_col=[]
        for j in range(X_train_sfs.shape[1]):
            keep_col.append(j)
            if j==0:
                continue
            else:
                for m in range(j):
                    r_coef=pearsonr(X_train_sfs[:,m],X_train_sfs[:,j])[0]
                    if r_coef>=0.5:
                        keep_col.remove(j)
                        break

        X_train_sfs=X_train_sfs[:,keep_col]
        X_test_sfs=X_test_sfs[:,keep_col]
        print('feat=',i+1,'keep_col=',len(keep_col))

        X_train=np.concatenate((X_train_gcca,X_train_sfs), axis=1)
        X_test=np.concatenate((X_test_gcca,X_test_sfs), axis=1)

    elif model=='KGCCA':
        kgcca=None
        kgcca=KGCCA(latent_dims=i+1)
        # gcca.fit(X_train_imputed[:,0:166],X_train_imputed[:,166:229],X_train_imputed[:,229:232])
        X_train_f,X_train_d,X_train_e=kgcca.fit_transform((X_train_imputed[:,0:166],X_train_imputed[:,166:229],X_train_imputed[:,229:232]))
        X_train=np.concatenate((X_train_f,X_train_d), axis=1)
        X_train=np.concatenate((X_train,X_train_e), axis=1)
        X_test_f,X_test_d,X_test_e=kgcca.transform((X_test_imputed[:,0:166],X_test_imputed[:,166:229],X_test_imputed[:,229:232]))
        X_test=np.concatenate((X_test_f,X_test_d), axis=1)
        X_test=np.concatenate((X_test,X_test_e), axis=1)

    elif model=='CCA+SFS':
        # Fix feats in one model, sweep feats in other
        cca=None
        cca=CCA(n_components=fixed_feat)
        X_train_f,X_train_d=cca.fit_transform(X_train_2[:,0:166],X_train_2[:,166:229])
        # X_train_f,X_train_d=cca.fit_transform(X_train_2[:,0:166],X_train_2[:,229:232])
        X_train_cca=np.concatenate((X_train_f,X_train_d), axis=1)
        X_test_f,X_test_d=cca.transform(X_test_2[:,0:166],X_test_2[:,166:229])
        # X_test_f,X_test_d=cca.transform(X_test_2[:,0:166],X_test_2[:,229:232])
        X_test_cca=np.concatenate((X_test_f,X_test_d), axis=1)

        # Get the number of features from your dataset for each variable set
        n_features_X = X_train_imputed[:,0:166].shape[1]  # Assuming X is your first variable set
        n_features_Y = X_train_imputed[:,166:229].shape[1]  # Assuming Y is your second variable set

        # Calculate total number of parameters in CCA
        cca_parameters = 2 * (n_features_X + n_features_Y) * cca.n_components

        # print(sum(p.numel() for p in scaler.parameters()))
        print('\n cca_parameters: ',cca_parameters)

        
        sfs=None
        sfs=SequentialFeatureSelector(clf, direction=direction, scoring='roc_auc', n_features_to_select=i+1)
        X_train_sfs=sfs.fit_transform(X_train_imputed,y_train)
        X_test_sfs=sfs.transform(X_test_imputed)

        # removing features above a certain mutual correlation coefficient
        keep_col=[]
        for j in range(X_train_sfs.shape[1]):
            keep_col.append(j)
            if j>0:
                for m in range(j):
                    r_coef=pearsonr(X_train_sfs[:,m],X_train_sfs[:,j])[0]
                    if r_coef>=rho:
                        keep_col.remove(j)
                        break

        X_train_sfs=X_train_sfs[:,keep_col]
        X_test_sfs=X_test_sfs[:,keep_col]
        print('feat=',i+1,'keep_col=',len(keep_col))

        X_train=np.concatenate((X_train_cca,X_train_sfs), axis=1)
        X_test=np.concatenate((X_test_cca,X_test_sfs), axis=1)
#%%
        # # removing features above a certain mutual correlation coefficient
        # keep_col=[]
        # for j in range(X_train.shape[1]):
        #     keep_col.append(j)
        #     if j<2*fixed_feat:
        #         continue
        #     else:
        #         for m in range(j):
        #             r_coef=pearsonr(X_train[:,m],X_train[:,j])[0]
        #             mi_coef=mutual_info_score(X_train[:,m],X_train[:,j])[0]
        #             if r_coef>=0.5:
        #                 keep_col.remove(j)
        #                 break

        # X_train=X_train[:,keep_col]
        # X_test=X_test[:,keep_col]
        # print('feats=',i+1+2*fixed_feat,'keep_col=',len(keep_col))
#%%
    elif model=='CCA+SMIG':
        # Fix feats in one model, sweep feats in other
        cca=None
        cca=CCA(n_components=fixed_feat)
        X_train_f,X_train_d=cca.fit_transform(X_train_2[:,0:166],X_train_2[:,166:229])
        X_train_cca=np.concatenate((X_train_f,X_train_d), axis=1)
        X_test_f,X_test_d=cca.transform(X_test_2[:,0:166],X_test_2[:,166:229])
        X_test_cca=np.concatenate((X_test_f,X_test_d), axis=1)

        # Get the number of features from your dataset for each variable set
        n_features_X = X_train_imputed[:,0:166].shape[1]  # Assuming X is your first variable set
        n_features_Y = X_train_imputed[:,166:229].shape[1]  # Assuming Y is your second variable set

        # Calculate total number of parameters in CCA
        cca_parameters = 2 * (n_features_X + n_features_Y) * cca.n_components

        # print(sum(p.numel() for p in scaler.parameters()))
        print('\n cca_parameters: ',cca_parameters)

        smig=None
        smig=MMINet(input_dim=232, output_dim=i+1, net='linear')
        smig.learn(X_train_imputed, y_train, num_epochs=10)
        X_train_smig = smig.reduce(X_train_imputed)
        X_test_smig = smig.reduce(X_test_imputed)

        # removing features above a certain mutual correlation coefficient
        keep_col=[]
        for j in range(X_train_smig.shape[1]):
            keep_col.append(j)
            if j==0:
                continue
            else:
                for m in range(j):
                    r_coef=pearsonr(X_train_smig[:,m],X_train_smig[:,j])[0]
                    if r_coef>=0.5:
                        keep_col.remove(j)
                        break

        X_train_smig=X_train_smig[:,keep_col]
        X_test_smig=X_test_smig[:,keep_col]
        print('feat=',i+1,'keep_col=',len(keep_col))

        X_train=np.concatenate((X_train_cca,X_train_smig), axis=1)
        X_test=np.concatenate((X_test_cca,X_test_smig), axis=1)

    clf.fit(X_train,y_train)

    # Count parameters in the pipeline
    # num_pipeline_parameters = count_pipeline_parameters(clf)
    # print("Number of parameters in the pipeline:", num_pipeline_parameters)

    # classifier = clf.named_steps['svc']
    # # Get estimator parameters
    # params = classifier.get_params()
    # # Count the number of parameters
    # num_parameters = len(params)
  

    ada = clf.named_steps['adaboostclassifier']
    # Calculate total number of parameters:
    # Each stump has 2 parameters (the feature threshold for splitting and 
    # the output value for each leaf), assuming binary classification.
    parameters_per_stump = 2

    # Plus one weight parameter per estimator in the ensemble
    parameters_for_weights = ada.n_estimators

    total_parameters = ada.n_estimators * parameters_per_stump + parameters_for_weights

    print("Total Parameters in Default AdaBoost:", total_parameters)

    # # Get number of support vectors for each class
    # # n_support_vectors = clf.support_vectors_.shape[0]
    # n_support_vectors = classifier.support_vectors_.shape[0]

    # # Get number of features from your dataset
    # n_features = X_train.shape[1]

    # # Calculate total number of parameters for support vector coefficients
    # parameters_for_support_vectors = n_support_vectors * n_features

    # # Calculate total number of intercepts 
    # # Note: This applies to multi-class classification; it's simply 1 for binary classification.
    # num_classes = len(clf.classes_)
    # intercepts = num_classes * (num_classes - 1) / 2 if num_classes > 2 else 1

    # # Total parameters are sum of both calculations above
    # total_parameters = parameters_for_support_vectors + intercepts

    # # print(sum(p.numel() for p in scaler.parameters()))
    # print('\n svc_parameters: ',total_parameters)
    
    # print(sum(p.numel() for p in clf.parameters()))

    # f = lambda x: clf.predict_proba(x)[:,1]
    # med = np.median(X_train, axis=0).reshape(1, -1)
    # explainer = shap.Explainer(f, med)
    # shap_values = explainer.shap_values(X_test)
    # shap.plots.beeswarm(shap_values)
    y_pred=clf.predict(X_test)
    # y_proba=clf.predict_proba(X_test)

    score, permutation_scores, pvalue = permutation_test_score(clf, X_train, y_train, random_state=seed_value)

    # ROC-AUC plot
    viz = RocCurveDisplay.from_estimator(
        clf,
        X_test,
        y_test,
        name="ROC fold {}".format(k+1),
        alpha=0.3,
        lw=1,
        ax=ax,
    )

    if model=='CCA+SFS':
        # return y_pred,viz.fpr,viz.tpr,viz.roc_auc,X_train_sfs
        return y_pred,viz.fpr,viz.tpr,viz.roc_auc,X_test,pvalue
    else:
        return y_pred,viz.fpr,viz.tpr,viz.roc_auc,X_test,pvalue
        # return y_pred,viz.fpr,viz.tpr,viz.roc_auc,X_test,y_proba

def plot_manifold(output_path,model,X,y,text,options,
                    imputer='KNN',neighbors=3,fixed_feat=0):

    
    fmri_feat=['Neg','Pos','Ov']
    j=0
    for key in fmri_feat:
        j+=1
        if options=='X_test':
            X_df_imputed=X
        elif options=='no_impute':
            X_df_imputed=X
        else:
            X_df_imputed=impute_data(imputer,X,fmri_key=j, neighbors=neighbors)

        manifold = MDS(n_components=3)
        results = manifold.fit_transform(X_df_imputed)

        # fig, ax = plt.subplots()
        ax = plt.figure(figsize=(8,8)).gca(projection='3d')
        cm = plt.cm.viridis

        # For 3-D
        scat = ax.scatter(
            xs=results[:,0], 
            ys=results[:,1], 
            zs=results[:,2], 
            c=y,
            s=100,
            cmap=cm)

        # For 2-D
        # scat = ax.scatter(
        #     x=results[:,0], 
        #     y=results[:,1], 
        #     c=y,
        #     cmap=cm)
        legend_elem = [Line2D([0], [0], marker='o', color=cm(0.),lw=0,label='No Seizure'),
                        Line2D([0], [0], marker='o', color=cm(1.),lw=0,label='Late Seizure')]

        legend1 = ax.legend(handles=legend_elem,
                            loc="upper right")

        ax.add_artist(legend1)
        ax.set_xlabel('Component-1')
        ax.set_ylabel('Component-2')
        ax.set_zlabel('Component-3')

        plt.tight_layout()     
        plt.savefig(output_path+'_plot/'+model+'_'+key+'_'+imputer+'_'+str(neighbors)+'_fixed_'+str(fixed_feat)+text+'_manifold.png')     
# %%

def count_parameters(estimator):
    # Get estimator parameters
    params = estimator.get_params()
    # Count the number of parameters
    num_parameters = len(params)
    return num_parameters

def count_pipeline_parameters(pipeline):
    # Initialize total number of parameters
    total_parameters = 0
    # Iterate over the steps in the pipeline
    for step_name, estimator in pipeline.named_steps.items():
        # Count parameters for each estimator
        num_parameters = count_parameters(estimator)
        # Accumulate total parameters
        total_parameters += num_parameters
    return total_parameters