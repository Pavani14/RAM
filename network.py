import keras
from keras import backend as K
from keras import layers
import numpy as np

class RAM():

    def __init__(self, totalSensorBandwidth, batch_size):

        self.discounted_r = np.zeros((batch_size, 1))
        self.output_dim = 10
        self.totalSensorBandwidth = totalSensorBandwidth
        self.batch_size = batch_size
        self.big_net()


      #  self.ram = self.core_network()
      #  self.gl_net = self.glimpse_network()
      #  self.act_net = self.action_network()
      #  self.loc_net = self.location_network()
    def REINFORCE_loss(self, action_p):
        def rloss(y_true, y_pred):
            log_l = K.log(action_p) * y_true
            return K.sum(y_pred - y_pred, axis=-1) + K.mean(- log_l)
        return rloss

#    def REINFORCE_loss(self, y_true, y_pred):
#       #     action = np.argmax(action_p, axis=-1)
#       #     if np.equal(action, y_true):
#        #assert y_pred.shape[-1] == 10, "Predicted Value should be class probability {}".format(y_pred.shape)
#        max_p_y = np.argmax(y_pred[0], axis=-1)
#
#        #R = np.cast(np.equal(max_p_y, y_true[0]), tf.float32) # reward per example
#
#        #reward = np.reduce_mean(R) # overall reward
#        action_p = y_pred[0] * y_true[0]
#        log_action_prob = K.log(y_pred[0]) * y_true[0]
#        loss = - log_action_prob #* self.discounted_r
#        return K.sum(y_pred[1], axis=-1)
    def penalized_loss(self,noise):
        def loss(y_true, y_pred):
            return K.mean(K.square(y_pred - y_true) - K.square(y_true - noise), axis=-1)

        return loss

    def big_net(self):
        glimpse_model_i = keras.layers.Input(batch_shape=(self.batch_size, self.totalSensorBandwidth),
                                             name='glimpse_input')
        glimpse_model = keras.layers.Dense(128, activation='relu')(glimpse_model_i)
        glimpse_model_out = keras.layers.Dense(256)(glimpse_model)

        location_model_i = keras.layers.Input(batch_shape=(self.batch_size, 2),
                                              name='location_input')
        location_model = keras.layers.Dense(128,
                                            activation = 'relu'
                                            )(location_model_i)
        location_model_out = keras.layers.Dense(256)(location_model)

        model_merge = keras.layers.add([glimpse_model_out, location_model_out])
        glimpse_network_output = keras.layers.Dense(256,
                                                    activation='relu')(model_merge)
        rnn_input = keras.layers.Reshape([256,1])(glimpse_network_output)
        model = keras.layers.recurrent.LSTM(256, activation='relu', use_bias=True, kernel_initializer='glorot_uniform',
                                         recurrent_initializer='orthogonal', bias_initializer='zeros',
                                         kernel_regularizer=None, recurrent_regularizer=None, bias_regularizer=None,
                                         activity_regularizer=None, kernel_constraint=None, recurrent_constraint=None,
                                         bias_constraint=None, dropout=0.0, recurrent_dropout=0.0,
                                         return_sequences=False, return_state=False, go_backwards=False, stateful=True,
                                         unroll=False, name = 'rnn')(rnn_input)
    #    model = keras.layers.recurrent.SimpleRNN(256, activation='relu', use_bias=True, kernel_initializer='glorot_uniform',
    #                                     recurrent_initializer='orthogonal', bias_initializer='zeros',
    #                                     kernel_regularizer=None, recurrent_regularizer=None, bias_regularizer=None,
    #                                     activity_regularizer=None, kernel_constraint=None, recurrent_constraint=None,
    #                                     bias_constraint=None, dropout=0.0, recurrent_dropout=0.0,
    #                                     return_sequences=False, return_state=False, go_backwards=False, stateful=True,
    #                                     unroll=False, name = 'rnn')(rnn_input)
        action_out = keras.layers.Dense(10,
                                 activation='softmax',
                                 name='action_output'
                                 )(model)
        location_out = keras.layers.Dense(2,
                                 activation='tanh',
                                 name='location_output'

                                 )(model)

        bmodel = keras.models.Model(inputs=[glimpse_model_i, location_model_i], outputs=[action_out, location_out])


        #bmodel.compile(optimizer=keras.optimizers.SGD(lr=0.01, momentum=0.0, decay=0.0, nesterov=False),
        #               loss=[self.cat_ent, self.REINFORCE_loss], loss_weights=[[1.,0.],[0.,0.]])
        bmodel.compile(optimizer=keras.optimizers.SGD(lr=0.01, momentum=0.0, decay=0.0, nesterov=False),
                       loss={'action_output': 'categorical_crossentropy',
                             'location_output': self.REINFORCE_loss(action_p=action_out)})
        self.ram = bmodel
        #model.compile(optimizer=keras.optimizers.SGD(lr=0.01, momentum=0.9, decay=0.0, nesterov=False), loss='categorical_crossentropy')

    def cat_ent(self, y_true, y_pred):
        return K.categorical_crossentropy(y_true, y_pred)




    def train(self, zooms, loc, true_a):
        #self.discounted_r = np.zeros((self.batch_size, 1))
        #for b in range(self.batch_size):
        #    self.discounted_r[b] = np.sum(self.compute_discounted_R(r[b], .99))

        glimpse_input = np.reshape(zooms, (self.batch_size, self.totalSensorBandwidth))
        loc_input = np.reshape(loc, (self.batch_size, 2))
        ath = self.dense_to_one_hot(true_a)
        self.ram.fit({'glimpse_input': glimpse_input, 'location_input': loc_input},
                                {'action_output': ath, 'location_output': ath}, epochs=1, batch_size=self.batch_size, verbose=0, shuffle=False)

        #self.ram.reset_states()

   # def __build_train_fn_REINFORCE(self):
   #     """Create a train function
   #     It replaces `model.fit(X, y)` because we use the output of model and use it for training.
   #     For example, we need action placeholder
   #     called `action_one_hot` that stores, which action we took at state `s`.
   #     Hence, we can update the same action.
   #     This function will create
   #     `self.train_fn([state, action_one_hot, discount_reward])`
   #     which would train the model.
   #     """

   #     print self.ram.trainable_weights
   #     action_prob_placeholder = self.ram.output[0]
   #     action_onehot_placeholder = K.placeholder(dtype=K.tf.float32, shape=(self.batch_size, self.output_dim),
   #                                               name="action_onehot")
   #   #  discount_reward_placeholder = K.placeholder(shape=(None, ),
   #   #                                              name="discount_reward")

   #     #TODO: Summation is wrong?
   #     #action_prob = K.sum(action_prob_placeholder * action_onehot_placeholder, axis=1)
   #     #log_action_prob = K.log(action_prob)
   #     log_action_prob = K.log(action_prob_placeholder) * action_onehot_placeholder

   #     loss = - log_action_prob #* discount_reward_placeholder
   #     loss = K.mean(loss)


   #     opt = keras.optimizers.sgd(momentum=0.)

   #    # updates = opt.get_updates(params=self.ram.trainable_weights,
   #    #                            loss='mse')

   #    # self.train_fn = keras.function(inputs=[self.ram.input,
   #    #                                    action_onehot_placeholder],
   #    #                                   # discount_reward_placeholder],
   #    #                            outputs=[],
   #    #                            updates=updates)

   #     updates_loc_net = opt.get_updates(params=self.ram.trainable_weights,#self.ram.get_layer(name='location_output').trainable_weights,
                                 #  constraints=[],
#                                   loss=loss)

#        self.train_fn_loc_net = K.function(inputs=[self.ram.input,
#                                               action_onehot_placeholder],
                                               #discount_reward_placeholder],
 #                                      outputs=[],
#                                       updates=updates_loc_net)

    def compute_discounted_R(self, R, discount_rate=.99):
        """Returns discounted rewards
        Args:
            R (1-D array): a list of `reward` at each time step
            discount_rate (float): Will discount the future value by this rate
        Returns:
            discounted_r (1-D array): same shape as input `R`
                but the values are discounted
        Examples:
            >>> R = [1, 1, 1]
            >>> self.compute_discounted_R(R, .99) # before normalization
            [1 + 0.99 + 0.99**2, 1 + 0.99, 1]
        """
        discounted_r = np.zeros_like(R, dtype=np.float32)
        running_add = 0
        for t in reversed(range(len(R))):
            running_add = running_add * discount_rate + R[t]
            discounted_r[t] = running_add

        #discounted_r -= discounted_r.mean() / discounted_r.std()

        return discounted_r



    def dense_to_one_hot(self, labels_dense, num_classes=10):
        """Convert class labels from scalars to one-hot vectors."""
        # copied from TensorFlow tutorial
        num_labels = labels_dense.shape[0]
        index_offset = np.arange(num_labels) * num_classes
        labels_one_hot = np.zeros((num_labels, num_classes))
        labels_one_hot.flat[index_offset + labels_dense.ravel()] = 1
        return labels_one_hot

    def choose_action(self,X,loc):

        glimpse_input = np.reshape(X, (self.batch_size, self.totalSensorBandwidth))
        return self.ram.predict_on_batch({"glimpse_input": glimpse_input, 'location_input': loc})
        #gl_out = self.gl_net.predict_on_batch([glimpse_input, loc])
        #ram_out = self.ram.predict_on_batch(np.reshape(gl_out, (self.batch_size, 1, 256)))
       # print self.act_net.predict_on_batch(ram_out)
       # print self.loc_net.predict_on_batch(ram_out)

        #return self.act_net.predict_on_batch(ram_out), self.loc_net.predict_on_batch(ram_out), ram_out, gl_out


    def get_best_action(self,prob_a):
        return np.argmax(prob_a)

def main():
    totalSensorBandwidth = 3 * 8 * 8 * 1
    ram = RAM(totalSensorBandwidth, 32)


if __name__ == '__main__':
    main()

