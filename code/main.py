# coding=utf8


'''
'''



import os
import sys
import time
import json
import traceback
import numpy as np
from glob import glob
from tqdm import tqdm
from tools import parse, py_op
from sklearn import metrics

# torch
import torch
import torchvision
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
import torch.backends.cudnn as cudnn
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt


import loss
import models
import function
import loaddata
# import framework
from loaddata import dataloader
from models import lstm
from models import GRU
from models import lstm_tunning
import plots


args = parse.args
args.hard_mining = 0
args.gpu = 1
args.use_trend = max(args.use_trend, args.use_value)
args.use_value = max(args.use_trend, args.use_value)
args.rnn_size = args.embed_size
args.hidden_size = args.embed_size
args.model = 'LSTM' # GRU or LSTM or LSTM_tunning

def train_eval(p_dict, phase='train'):

    epoch = p_dict['epoch']
    model = p_dict['model']
    loss = p_dict['loss']
    if phase == 'train':
        data_loader = p_dict['train_loader']
        optimizer = p_dict['optimizer']
    else:
        data_loader = p_dict['val_loader']


    classification_metric_dict = dict()
    for i,data in enumerate(tqdm(data_loader)):
        if args.use_visit:
            if args.gpu:
                data = [ Variable(x.cuda()) for x in data ]
            visits, values, mask, master, labels, times, trends  = data
            if i == 0:
                print('input size', visits.size())
            output = model(visits, master, mask, times, phase, values, trends)
        else:
            inputs = Variable(data[0].cuda())
            labels = Variable(data[1].cuda())
            output = model(inputs)


        if args.task == 'task2':
            output, mask, time = output
            labels = labels.unsqueeze(-1).expand(output.size()).contiguous()
            labels[mask==0] = -1
        else:
            time = None

        classification_loss_output = loss(output, labels, args.hard_mining)
        loss_gradient = classification_loss_output[0]

        function.compute_metric(output, labels, time, classification_loss_output, classification_metric_dict, phase)


        if phase == 'train':
            optimizer.zero_grad()
            loss_gradient.backward()
            optimizer.step()



    print('\nEpoch: {:d} \t Phase: {:s} \n'.format(epoch, phase))
    metric= function.print_metric('classification', classification_metric_dict, phase)
    if args.phase != 'train':
        print('metric = ', metric)
        print()
        print()
        return
    if phase == 'val':
        if metric > p_dict['best_metric'][0]:
            p_dict['best_metric'] = [metric, epoch]
            function.save_model(p_dict)
            if 0:
                preds = classification_metric_dict['preds'] 
                labels = classification_metric_dict['labels'] 
                times = classification_metric_dict['times'] 
                fl = open('../result/tauc_label.csv', 'w')
                fr = open('../result/tauc_result.csv', 'w')
                fl.write('adm_id,last_event_time,mortality\n')
                fr.write('adm_id,probability\n')
                for i, (p,l,t) in enumerate(zip(preds, labels, times)):
                    if i % 30:
                        continue
                    fl.write(str(i) + ',')
                    fl.write(str(t) + ',')
                    fl.write(str(int(l)) + '\n')

                    fr.write(str(i) + ',')
                    fr.write(str(p) + '\n')


        print('valid: metric: {:3.4f}\t epoch: {:d}\n'.format(metric, epoch))

        print('\t\t\t valid: best_metric: {:3.4f}\t epoch: {:d}\n'.format(p_dict['best_metric'][0], p_dict['best_metric'][1]))  
    else:
        print('train: metric: {:3.4f}\t epoch: {:d}\n'.format(metric, epoch))
    return metric



def main():
    p_dict = dict() # All the parameters
    p_dict['args'] = args
    args.split_nn = args.split_num + args.split_nor * 3
    args.vocab_size = args.split_nn * 145 + 1
    print('vocab_size', args.vocab_size)

    ### load data
    print('read data ...')
    patient_time_record_dict = py_op.myreadjson(os.path.join(args.result_dir, 'patient_time_record_dict.json'))
    patient_master_dict = py_op.myreadjson(os.path.join(args.result_dir, 'patient_master_dict.json'))
    patient_label_dict = py_op.myreadjson(os.path.join(args.result_dir, 'patient_label_dict.json'))

    patient_train = list(json.load(open(os.path.join(args.file_dir, args.task, 'train.json'))))
    patient_valid = list(json.load(open(os.path.join(args.file_dir, args.task, 'val.json')))) 

    if len(patient_train) > len(patient_label_dict):
        patients = list(patient_time_record_dict.keys())
        patients = list(patient_label_dict.keys())
        n = int(0.8 * len(patients))
        patient_train = patients[:n]
        patient_valid = patients[n:]





    print('data loading ...')
    train_dataset  = dataloader.DataSet(
                patient_train, 
                patient_time_record_dict,
                patient_label_dict,
                patient_master_dict, 
                args=args,
                phase='train')
    train_loader = DataLoader(
                dataset=train_dataset, 
                batch_size=args.batch_size,
                shuffle=True, 
                num_workers=8, 
                pin_memory=True)
    val_dataset  = dataloader.DataSet(
                patient_valid, 
                patient_time_record_dict,
                patient_label_dict,
                patient_master_dict, 
                args=args,
                phase='val')
    val_loader = DataLoader(
                dataset=val_dataset, 
                batch_size=args.batch_size,
                shuffle=False, 
                num_workers=8, 
                pin_memory=True)

    p_dict['train_loader'] = train_loader
    p_dict['val_loader'] = val_loader



    cudnn.benchmark = True

    if args.model == 'GRU':
        net = GRU.GRU(args)
    elif args.model == 'LSTM':
        net = lstm.LSTM(args)
    elif args.model == 'LSTM_tunning':
        net = lstm.LSTM(args)

    if args.gpu:
        net = net.cuda()
        p_dict['loss'] = loss.Loss().cuda()
    else:
        p_dict['loss'] = loss.Loss()

    parameters = []
    for p in net.parameters():
        parameters.append(p)
    optimizer = torch.optim.Adam(parameters, lr=args.lr)
    p_dict['optimizer'] = optimizer
    p_dict['model'] = net
    start_epoch = 0

    p_dict['epoch'] = 0
    p_dict['best_metric'] = [0, 0]


    ### resume pretrained model
    if os.path.exists(args.resume):
        print('resume from model ' + args.resume)
        function.load_model(p_dict, args.resume)
        print('best_metric', p_dict['best_metric'])
        # return


    if args.phase == 'train':

        best_f1score = 0
        train_losses=[]
        train_f1score=[]
        valid_losses=[]
        valid_f1score= []
        for epoch in range(p_dict['epoch'] + 1, args.epochs):
            p_dict['epoch'] = epoch
            for param_group in optimizer.param_groups:
                param_group['lr'] = args.lr
            metric_train=train_eval(p_dict, 'train')
            metric_valid=train_eval(p_dict, 'val')
            train_f1score.append(metric_train)
            valid_f1score.append(metric_valid)
        max_f1_train=max(train_f1score)
        max_f1_valid = max(valid_f1score)
        plt.plot(train_f1score, label='Training f1 Score')
        plt.plot([max_f1_train]*(p_dict['epoch'] + 1), label='Training Max f1 Score: '+str(round(max_f1_train,4)))
        plt.plot(valid_f1score, label='Validation f1 Score')
        plt.plot([max_f1_valid]*(p_dict['epoch'] + 1), label='Validation Max f1 Score: '+str(round(max_f1_valid,4)))
        plt.legend()
        plt.xlabel("epoch")
        plt.ylabel('f1 Score')
        plt.title('f1 Score '+args.model)
        plt.savefig('f1 Score_Curve_'+args.model+'.png')
        plt.cla()
        #




if __name__ == '__main__':
    main()
