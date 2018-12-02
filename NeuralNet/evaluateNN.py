import os, sys
# sys.path.append(os.path.join(os.getcwd()))
import tensorflow as tf
from tensorflow import keras
import DB_index_pull as db_pull
import numpy as np
# from keras.utils import np_utils
from tensorflow.keras.wrappers.scikit_learn import KerasClassifier
from sklearn.model_selection import KFold
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import random
import final_output as fo
random.seed(7)



def db_getlabel(input):
    if input == "variable":
        return 1
    elif input == "print":
        return 2
    elif input == "loop":
        return 3
    elif input == "if":
        return 4
    else:
        return -1


# reads sentences from filename
# returns a list of Series of words in the sentence
#   each index of list is one sentence
def read_sentences(filename):
    return pd.read_csv("data/" + filename)["sen"], pd.read_csv("data/" + filename)["cat"]


# parse input through a file
# sentences returns the list of series words in each sentence
def parse_input(filename):
    sentences, targets = read_sentences(filename)
    indices, wordlist, poslist = db_pull.in_pipe(sentences)
    # pad sequences to the same length
    indices = pd.DataFrame.from_dict(keras.preprocessing.sequence.pad_sequences(indices, 10, padding='post'))
    poslist = pd.DataFrame.from_dict(keras.preprocessing.sequence.pad_sequences(poslist, 10, padding='post'))
    # print(len(indices))
    # print(len(wordlist))
    # print(len(poslist))
    # TODO: assert to confirm shape of dataframes
    return indices, poslist, targets
#  Categories:
#  1: variable
#  2: print
#  3: loop
#  4: if

# training data
# if_indices, if_poslist, if_targets = parse_input("if_data.csv")
variable_indices, variable_poslist, variable_targets = parse_input("variable_data.csv")
print_indices, print_poslist, print_targets = parse_input("print_data.csv")
loop_indices, loop_poslist, loop_targets = parse_input("loop_data.csv")

#concatenate data to a meaningful shape for the neural network
id_list = pd.concat([variable_indices, print_indices, loop_indices], axis=0, ignore_index=True)
pos_list = pd.concat([variable_poslist, print_poslist, loop_poslist], axis=0, ignore_index=True)

input_data = pd.concat([id_list, pos_list], axis=1, ignore_index=True)
input_labels = pd.concat([variable_targets, print_targets, loop_targets], axis=0, ignore_index=True)


train_data = pd.DataFrame()
train_labels = pd.Series()
# validation_data = pd.DataFrame()
# validation_labels = pd.Series()
test_data = pd.DataFrame()
test_labels = pd.Series()

shuffled_data = pd.DataFrame.reset_index(pd.DataFrame.sample(pd.concat([input_data, input_labels],
                                                                       axis=1, ignore_index=True),
                                                             frac=1), drop=True)
train_labels = shuffled_data[20]
train_data = shuffled_data.drop(columns=[20])
train_data, test_data = np.split(train_data, [int(.9*len(train_data))])
# TODO: onehot encoding for labels
# encode class values as integers
encoder = LabelEncoder()
encoder.fit(train_labels)
encoded_labels = encoder.transform(train_labels)
# convert integers to dummy variables (i.e. one hot encoded)
encoded_labels = keras.utils.to_categorical(encoded_labels)
train_labels, test_labels = np.split(encoded_labels, [int(.9*len(encoded_labels))])



print(test_data.shape)
print(test_labels.shape)
# print(validation_data.shape)
# print(validation_labels.shape)
print(train_data.shape)
print(train_labels.shape)

# Build the model
# vocab_size is the size of our database at model initialization.
# this ensures that all new words have already been added to the database.
vocab_size = db_pull.db_len

model = keras.Sequential()
# Input Layer
model.add(keras.layers.Embedding(vocab_size, 64, input_length=20))
#   Outputs shape=
model.add(keras.layers.GlobalAveragePooling1D())
#   Outputs 1D shape=
# Hidden Layer
model.add(keras.layers.Dense(64, activation=tf.nn.relu))
# Output Layer: needs as many nodes as there are categories.
model.add(keras.layers.Dense(3, activation='softmax'))

print(model.summary())
model.compile(optimizer=tf.train.AdamOptimizer(),
              loss='categorical_crossentropy',
              metrics=['accuracy']) # consider RMSE or MSE as metric for error

#  Train the model

history = model.fit(x=train_data,
                    y=train_labels,
                    epochs=10,
                    batch_size=512,
                    validation_split=0.1,
                    # validation_data=(validation_data, validation_labels),
                    verbose=1)
print(history)
results = model.evaluate(test_data, test_labels)

print(results)

def makePrediction(sentence):
    (indices, wordlist, poslist) = db_pull.in_pipe([sentence])
    id_list = pd.DataFrame.from_dict(keras.preprocessing.sequence.pad_sequences(indices, 10, padding='post'))
    pos_list = pd.DataFrame.from_dict(keras.preprocessing.sequence.pad_sequences(poslist, 10, padding='post'))
    input_data = pd.concat([id_list, pos_list], axis=1, ignore_index=True)
    prediction = model.predict(pd.DataFrame(data=input_data))
    print("-------")
    best=0
    best_i=0
    i=0
    print(prediction)
    for i in range(0,3):
        value = prediction[0][i]
        print(value)
        if (value >= best):
            best=value
            best_i=i
    # print(best_i)
    if best_i == 1:
        obj1, obj2 = fo.varObject(sentence)
        print(fo.varCode(obj1, obj2))
    elif best_i == 2:
        obj1 = fo.printObject(sentence)
        print(fo.printCode(obj1))
    elif best_i == 3:
        obj1 = fo.LoopObject(sentence)
        print(fo.loopCode(obj1))
    elif best_i == 4:
        obj1, opera, obj2 = fo.ifObject(sentence)
        print(fo.ifCode(obj1, opera, obj2))
    else:
        return -1
