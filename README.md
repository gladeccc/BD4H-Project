# DII-Challenge-2019
The early identification of sepsis cases.

# build the env
	
		pip install -r requirement.txt

# data preprocessing

-	creat result folder for data preprocessing results

		mkdir result
		mkdir data
		mkdir data/models

-	generate json files 

		cd preprocessing
		python gen_master_feature.py --master-file ../file/master.csv
		python gen_feature_time.py --vital-file ../file/vital.csv				# only for task1
		python gen_vital_feature.py --vital-file ../file/vital.csv
		python gen_label.py --label-file ../file/label.csv
		python gen_feature_order.py  --feature-order-file  ../file/feature_value_order_dict.json

#	train and validate the model, the best model will saved in ../data/models/
		
		python main.py --task case1		# for task1 case1
		python main.py --task task1		# for task1 case2
		python main.py --task task2		# for task2
		
#   if the model is LSTM, set LSTM in main.py, if the model is GRU, set the gru in main.py



#	You can also run the code by:

		python run.py --label-file ../file/label.csv --vital-file ../file/vital.csv --master-file  ../master.csv --task case1


#   result of F1 Score Plot will show in main.py


