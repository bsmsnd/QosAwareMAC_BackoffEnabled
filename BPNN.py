# import tensorflow as tf
import numpy as np
import math
import Parameters

# Number of neurons in hidden layer
M = 15
# PID implementation:
# P - 0, I - 1, D - Yes

# System Degree, take care to change this value because of silly implementation :)
D = 3


def f(x):
	return math.tanh(x)


def f_diff(x):
	return (1 - math.pow(f(x), 2)) / 2


def g(x,scale=50):
	return (math.tanh(x) + 1) / scale


def g_diff(x,scale=50):
	return (1 - math.tanh(x) * math.tanh(x)) / scale


class PIDWithBPNN:
	def __init__(self, expect_ratio):
		self.expect_ratio = expect_ratio
		self.actual_ratio = []
		self.__classes = len(expect_ratio)  # Number of classes
		self.error = np.array([[0 for _ in range(self.__classes)] for __ in range(3)])
		# weights & thresholds(bias) init.
		self.__weight1 = np.random.uniform(0, 1, size=(self.__classes, M, D))  # transposed matrix, i.e. W^T
		self.__weight2 = np.random.uniform(0, 1, size=(self.__classes, 3, M))
		self.__bias1 = np.random.uniform(0, 1, size=(self.__classes, 1, M))
		self.__bias2 = np.random.uniform(0, 1, size=(1, 3))
		self.__saveWeightChange1 = np.zeros(shape=(self.__classes, M, D))
		self.__saveWeightChange2 = np.random.uniform(0, 0.005, size=(self.__classes, 3, M))
		self.__count = 0

		# Some parameters that influences the learning process
		# 1. scale
		self.scale = 50
		# 2. learning rate (eta)
		self.eta = 0.01
		# 3. inertia coefficient (alpha)
		self.alpha = 0.01

	def save_mat(self):
		np.savez_compressed("save_para", weight1=self.__weight1, weight2=self.__weight2, c=self.__bias1,
							bias2=self.__bias2, saveWeightChange1=self.__saveWeightChange1,
							saveWeightChange2=self.__saveWeightChange2)

	def load_mat(self):
		with np.load('save_para.npz') as data:
			self.__weight1 = data['weight1']
			self.__weight2 = data['weight2']
			self.__bias1 = data['bias1']
			self.__bias2 = data['bias2']
			self.__saveWeightChange1 = data['saveWeightChange1']
			self.__saveWeightChange2 = data['saveWeightChange2']

	def train(self, actual_ratio):

		# l1 = addLayer(input_data=self.xs, in_size=self.inSize, out_size=M, activity_function=tf.tanh())
		# l2 = addLayer(input_data=l1, in_size=M, out_size=N, activity_function=g())
		# loss = tf.self.error
		# sess = tf.Session()
		# init = tf.initialize_all_variables()

		self.__count = self.__count + 1
		# last_input = self.input_data
		# self.input_data = possibility_distribution
		self.actual_ratio = actual_ratio
		cur_error = np.array(
			[self.actual_ratio[i] - self.expect_ratio[i] for i in range(self.actual_ratio.__len__())])
		cur_error.shape = (1, self.__classes)
		temp_error = np.concatenate((cur_error, self.error), axis=0)
		self.error = np.delete(temp_error, -1, axis=0)
		K = np.zeros(shape=(self.__classes, 3))
		if self.__count < 3:  # we need 3 consecutive outputs
			return K
		partial_diff = np.zeros(shape=(self.__classes, 3))
		# Partial Differential Matrix
		for j in range(self.__classes):
			partial_diff[j][0] = self.error[0][j] - self.error[1][j]
			partial_diff[j][1] = self.error[0][j]
			partial_diff[j][2] = self.error[0][j] - 2 * self.error[1][j] + self.error[2][j]
		# J = [(0.5 * self.error[i] * self.error[i]) for i in range(self.actual_ratio.__len__())]  # Useless?
		x = self.error
		# TODO: Standardization
		for classIndex in range(self.__classes):
			net_j = np.add(np.dot(self.__weight1[classIndex], x[:, classIndex]), self.__bias1[classIndex])
			hj = np.array([f(net_j[0][_]) for _ in range(M)])
			hj.shape = (hj.__len__(), 1)  # transpose
			net_s = np.dot(self.__weight2[classIndex], hj)
			t = [g(net_s[_], self.scale) for _ in range(3)]
			K[classIndex] = t  # for output

			# train next weight matrix
			delta_s = np.zeros(shape=(1, 3))
			for s in range(3):
				delta_s[0][s] = self.error[0][classIndex] * (-1) * partial_diff[classIndex][s] * g_diff(net_s[s][0], self.scale)
				for j in range(M):
					delta_weight_sj = self.eta * delta_s[0][s] * hj[j] + self.alpha * self.__saveWeightChange2[classIndex][s][j]
					self.__saveWeightChange2[classIndex][s][j] = delta_weight_sj
					self.__weight2[classIndex][s][j] += delta_weight_sj
			for j in range(M):
				delta_j = f_diff(net_j[0][j]) * np.dot(delta_s, self.__weight2[classIndex, :, j])
				for i in range(D):
					delta_weight_ji = self.eta * delta_j * hj[j] + self.alpha * self.__saveWeightChange1[classIndex][j][i]
					self.__saveWeightChange1[classIndex][j][i] = delta_weight_ji
					self.__weight2[classIndex][i][j] += delta_weight_ji

		# output
		return K
