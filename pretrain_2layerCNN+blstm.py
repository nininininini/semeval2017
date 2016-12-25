#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: xiwen zhao
@created: 2016.12.25
"""

from optparse import OptionParser
from pre_trainer import BasePreTrainer
from common import data_manager

from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Embedding, Merge
from keras.layers import LSTM, SimpleRNN, GRU
from keras.layers import Embedding
from keras.layers import Convolution1D, GlobalMaxPooling1D, MaxPooling1D
from keras.layers.convolutional import ZeroPadding1D
from keras.layers.wrappers import Bidirectional
from keras.optimizers import RMSprop, SGD


class Trainer(BasePreTrainer):
    def get_model_name(self):
        return __file__.split('/')[-1].split('.')[0]

    def post_prepare_X(self, x):
        return [x for _ in range(2)]

    def set_model_config(self, options):
        self.config = dict(
            nb_filter_pre_1 = options.nb_filter_pre_1,
            nb_filter_pre_2 = options.nb_filter_pre_2,
            filter_length_1 = options.filter_length_1,
            filter_length_2 = options.filter_length_2,
            dropout_W = options.dropout_W,
            dropout_U = options.dropout_U,
            optimizer = options.optimizer,
            rnn_output_dims_pre = options.rnn_output_dims_pre,
        )

    def get_optimizer(self, key_optimizer):
        if key_optimizer == 'rmsprop':
            return RMSprop(lr=0.001, rho=0.9, epsilon=1e-06)
        else:  # 'sgd'
            return SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=False)

    def build_pre_model(self, config, weights):
        blstm_model = Sequential()
        blstm_model.add(Embedding(config['max_features'],
                                  config['embedding_dims'],
                                  input_length = config['input_length'],
                                  weights = [weights['Wemb']] if 'Wemb' in weights else None))
        blstm_model.add(Bidirectional(LSTM(config['rnn_output_dims_pre'],
                                          dropout_W=config['dropout_W'], dropout_U=config['dropout_U'])))

        cnn_model = Sequential()
        cnn_model.add(Embedding(config['max_features'],
                                config['embedding_dims'],
                                input_length = config['input_length'],
                                weights = [weights['Wemb']] if 'Wemb' in weights else None))
                                #dropout = 0.2))

        cnn_model.add(Convolution1D(nb_filter = config['nb_filter_pre_1'],
                                    filter_length = config['filter_length_1'],
                                    border_mode = 'valid',
                                    activation = 'relu',
                                    subsample_length = 1))

        cnn_model.add(MaxPooling1D(pool_length=6, stride=2, border_mode='valid'))

        cnn_model.add(Convolution1D(nb_filter = config['nb_filter_pre_2'],
                                    filter_length = config['filter_length_2'],
                                    border_mode = 'valid',
                                    activation = 'relu',
                                    subsample_length = 1))

        cnn_model.add(GlobalMaxPooling1D())

        # merged model
        merged_model = Sequential()
        merged_model.add(Merge([blstm_model, cnn_model], mode='concat', concat_axis=1))

        merged_model.add(Dropout(0.25))
        merged_model.add(Dense(self.output_dims))
        print '<dense output dimension>:', self.output_dims

        merged_model.compile(loss=self.loss_type,
                             optimizer=self.get_optimizer(config['optimizer']),
                             metrics=['accuracy'])

        return merged_model


def main():
    optparser = OptionParser()
    optparser.add_option("-t", "--task", dest="key_subtask", default="D")
    optparser.add_option("-p", "--nb_epoch", dest="nb_epoch", type="int", default=50)
    optparser.add_option("-e", "--embedding", dest="fname_Wemb", default="glove.twitter.27B.25d.txt.trim")
    optparser.add_option("-d", "--hidden_dims", dest="hidden_dims", type="int", default=250)
    optparser.add_option("-f", "--nb_filter_1", dest="nb_filter_1", type="int", default=200)
    optparser.add_option("-F", "--nb_filter_2", dest="nb_filter_2", type="int", default=200)
    optparser.add_option("-r", "--rnn_output_dims", dest="rnn_output_dims_pre", type="int", default=100)
    optparser.add_option("-l", "--filter_length_1", dest="filter_length_1", type="int", default=6)
    optparser.add_option("-L", "--filter_length_2", dest="filter_length_2", type="int", default=3)
    optparser.add_option("-w", "--dropout_W", dest="dropout_W", type="float", default=0.25)
    optparser.add_option("-u", "--dropout_U", dest="dropout_U", type="float", default=0.25)
    optparser.add_option("-o", "--optimizer", dest="optimizer", default="rmsprop")
    opts, args = optparser.parse_args()

    trainer = Trainer(opts)
    trainer.pre_train()

if __name__ == '__main__':
    main()
