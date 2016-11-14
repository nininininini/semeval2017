'''This example demonstrates the use of Convolution1D for text classification.

Gets to 0.89 test accuracy after 2 epochs.
90s/epoch on Intel i5 2.4Ghz CPU.
10s/epoch on Tesla K40 GPU.

'''

from __future__ import print_function
import numpy as np
import data_manager
import input_adapter
import wordembed
np.random.seed(1337)  # for reproducibility

from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation
from keras.layers import Embedding
from keras.layers import Convolution1D, GlobalMaxPooling1D
from keras import backend as K



# set parameters:
max_features = 5000
maxlen = 45
batch_size = 32
embedding_dims = 25
nb_filter = 250
filter_length = 3
hidden_dims = 250
nb_epoch = 20

print('Loading data...')
key_subtask = 'B'
vocabs = data_manager.read_vocabs_topN(key_subtask, max_features)
max_features = len(vocabs)

text_indexer = input_adapter.get_text_indexer(vocabs)
label_indexer = input_adapter.get_label_indexer(key_subtask)

dataset = []
for mode in ['train', 'dev', 'devtest']:
    texts_labels = data_manager.read_texts_labels(key_subtask, mode)
    x, y = input_adapter.adapt_texts_labels(texts_labels, text_indexer, label_indexer)
    print(min(x))
    dataset.append((x, y))
exit()

dataset = tuple(dataset)  # list of 2 tuples --> tuple of tuple
train, dev, devtest = dataset
X_train, y_train = train
X_dev, y_dev = dev
X_test, y_test = devtest

Wemb = wordembed.get(vocabs, 'glove.twitter.27B.25d.txt', 25)  # list of numpy array
#print(len(Wemb), Wemb)


print(len(X_train), 'train sequences')
print(len(X_dev), 'development sequences')
print(len(X_test), 'test sequences')

print('Pad sequences (samples x time)')
X_train = sequence.pad_sequences(X_train, maxlen=maxlen)
X_dev = sequence.pad_sequences(X_dev, maxlen=maxlen)
X_test = sequence.pad_sequences(X_test, maxlen=maxlen)
print('X_train shape:', X_train.shape)
print('X_dev shape:', X_dev.shape)
print('X_test shape:', X_test.shape)

print('Build model...')
model = Sequential()

# we start off with an efficient embedding layer which maps
# our vocab indices into embedding_dims dimensions
model.add(Embedding(max_features,
                    embedding_dims,
                    input_length=maxlen,
                    weights=[Wemb],
                    dropout=0.2))

# we add a Convolution1D, which will learn nb_filter
# word group filters of size filter_length:
model.add(Convolution1D(nb_filter=nb_filter,
                        filter_length=filter_length,
                        border_mode='valid',
                        activation='relu',
                        subsample_length=1))
print(model.output_shape)
# we use max pooling:
model.add(GlobalMaxPooling1D())

# We add a vanilla hidden layer:
model.add(Dense(hidden_dims))
model.add(Dropout(0.2))
model.add(Activation('relu'))
print(model.output_shape)
# We project onto a single unit output layer, and squash it with a sigmoid:
model.add(Dense(1))
model.add(Activation('sigmoid'))


model.compile(loss='binary_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])
model.fit(X_train, y_train,
          batch_size=batch_size,
          nb_epoch=nb_epoch,
          validation_data=(X_dev, y_dev))

score, acc = model.evaluate(X_test, y_test,
                            batch_size=batch_size)
print('Test score:', score)
print('Test accuracy:', acc)  # 0.795589