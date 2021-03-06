import numpy as np
import os
import pickle
from scipy.misc import imread, imsave, imresize
from math import exp, log, sqrt
from random import randint


class Network:
    """
            NETWORK
    - layers : liste ou tableau de couches de neurones
    - depth : le nombre de couches
    - categories : classes prises en compte par le réseau
    > train : fonction train sur un tableau d'images et de labels
    > training : effectue train sur une série d'images
    > test : fonction test sur une image (ou un tableau d'images)
    """
    
    def __init__(self, name, layers_list, cat):
        self.id = name
        n = len(layers_list)
        self.depth = n
        self.layers = []

        # LAYERS
        Type, param = layers_list[0]
        self.layers.append(Input(param))
        for i in range(1, n):
            Type, param = layers_list[i]
            self.layers.append(Type(param, self.layers[i-1].size))
        FullyConnected.ident = 0
        Convolutionnal.ident = 0
        Pooling.ident = 0

        # CATEGORIES
        self.categories = [ "" for i in range(np.size(self.layers[n-1].output))]
        for i in range(min(len(cat), len(self.categories))):
            self.categories[i] = cat[i]


    def define(self):
        print("Network : " + self.id)
        print("Depth : " + str(self.depth))
        print("Categories : " + str(self.categories), end = '\n\n')
        for i in range(self.depth):
            if type(self.layers[i]) == FullyConnected or type(self.layers[i]) == Convolutionnal:
                self.layers[i].define(self.layers[i+1])
            if type(self.layers[i]) == Pooling or type(self.layers[i]) == Normal:
                self.layers[i].define()
    

    def train(self, example):
        n = self.depth
        image, expect = example
        self.layers[0].update(image)

        # propagation avant
        print("\n----------------------------------- FRONT : ------------------------------------------------")
        for i in range(1, n):
            self.layers[i].front(self.layers[i-1].output)

        # calcul de l'erreur
        self.layers[n-1].loss(expect, 1)

        # rétropropagation
        print("\n----------------------------------- BACK : -------------------------------------------------")
        for i in range(1, n):
            self.layers[n-i].back(self.layers[n-i-1])
        self.layers[n-1].term = np.zeros(np.shape(self.layers[n-1].term))


        # retour console
        print("\n----------------------------------- RESULT : -----------------------------------------------")
        out = np.reshape(self.layers[n-1].output, len(self.categories))
        for c in range(len(self.categories)):
            print("[" + str(expect[c]), end = "] [")
            print(str(out[c]) + "]")
        print(self.layers[n-1].error, end = "\n\n")


    def train_batch(self, example, nb_ex, batch_size):
        n = self.depth
        image, expect = example
        self.layers[0].update(image)

        # propagation avant
        print("\n----------------------------------- FRONT : ------------------------------------------------")
        for i in range(1, n):
            self.layers[i].front(self.layers[i-1].output)

        # calcul de l'erreur
        self.layers[n-1].loss(expect)

        if nb_ex % batch_size == 0 :
            # rétropropagation
            print("\n----------------------------------- BACK : -------------------------------------------------")
            self.layers[n-1].term /= batch_size
            for i in range(1, n):
                self.layers[n-i].back(self.layers[n-i-1])
            self.layers[n-i].term = np.zeros(np.shape(self.layers[n-i].term))


        # retour console
        print("\n----------------------------------- RESULT : -----------------------------------------------")
        out = np.reshape(self.layers[n-1].output, len(self.categories))
        for c in range(len(self.categories)):
            print("[" + str(expect[c]), end = "] [")
            print(str(out[c]) + "]")
        print(self.layers[n-1].error, end = "\n\n")
    

    def training(self, setup):
        i = 1
        for ex in setup :
            print("\n============================================= EX : " + str(i) + " =============================================")
            i += 1
            self.train(ex)


    def training_CIFAR(self, batch_nb, dist, batch_size):
        loaded = np.load("Data/batch_" + str(batch_nb) + ".npz")
        features, labels = loaded["f"], loaded["l"]
        start, end = dist
        for i in range(start, end):
            print("\n============================================= BATCH : " + str(batch_nb) + " - EX : " + str(i) + " =============================================")
            ex = (features[i], labels[i])
            self.train_batch(ex, i, batch_size)


    def test(self, image):
        n = self.depth
        self.layers[0].update(image)
        for i in range(1, n):
            self.layers[i].front(self.layers[i-1].output)
        print(self.layers[n-1].output)



class Input:
    """
            INPUT
    + s'occupe de la transition entre le réseau et les donneés
    - size : tuple des dimensions (D, H, W)
    - output : tableau des valeurs d'entrée
    > update : fait prendre à output une nouvelle valeur
    """
    def  __init__(self, parameters):
         self.id = "Input"
         self.rank = 0
         self.size = parameters
         self.output = np.zeros(self.size)
         self.term = np.zeros(self.size)

    def define(self):
        print(self.id, end = ' : ')
        print(self.size)

    def update(self, out):
        self.output = out


class FullyConnected:

    ident = 0

    def  __init__(self, parameters, prev_size): 
        FullyConnected.ident += 1
        D, H, W, rate = parameters
        D1, H1, W1 = prev_size
        self.id = "FullyConnected_n°" + str(FullyConnected.ident)
        self.size = (D, H, W)
        self.weigths = np.random.randn(D, H, W, D1, H1, W1) * 0.01 / sqrt(D1*H1*W1)
        self.delta = np.zeros((D, H, W, D1, H1, W1))
        self.bias = np.random.randn(D, H, W) * 0.01 / sqrt(D1*H1*W1)
        self.delta_bias = np.zeros(self.size)
        self.term = np.zeros(self.size)
        self.output = np.zeros(self.size)
        self.speed, self.moment, self.white = rate

    def define(self, next_layer):
        print(self.id + " - " + next_layer.id, end = " : ")
        print(self.size)

    def front(self, inp):
        self.output = np.sum(np.sum(np.sum(self.weigths[:, :, :] * inp, axis = 5), axis = 4), axis = 3) + self.bias
        # sortie :
        print("\n" + self.id)
        print("    out max : " + str(np.max(self.output)))
        print("        min : " + str(np.min(self.output)))
        print("weigths max : " + str(np.max(self.weigths)))
        print("        min : " + str(np.min(self.weigths)))
        print("   bias max : " + str(np.max(self.bias)))
        print("        min : " + str(np.min(self.bias)))

    def back(self, prev_layer):
        D, H, W = self.size
        # terme d'erreur :
        prev_layer.term = np.zeros(np.shape(prev_layer.term))
        prev_layer.term = np.sum(np.sum(np.sum(np.transpose(np.transpose(self.term) * np.transpose(self.weigths)), axis = 0), axis = 0), axis = 0)

        # biais :
                           # partie inertielle             # part d'erreur
        self.delta_bias = (self.moment*self.delta_bias) + (self.speed*self.term)
        self.bias += self.delta_bias

        # poids :
                      # partie inertielle        # white-decay
        self.delta = (self.moment*self.delta) - (self.white*self.speed*self.weigths)
        for d in range(D):
            for h in range(H):
                for w in range(W):
                                            # part d'erreur
                    self.delta[d, h, w] += (self.speed * prev_layer.output * self.term[d, h, w])
        self.weigths += self.delta
        # sortie :
        print("\n" + self.id)
        print("      term max : " + str(np.max(self.term)))
        print("           min : " + str(np.min(self.term)))
        print("     delta max : " + str(np.max(self.delta)))
        print("           min : " + str(np.min(self.delta)))
        print("delta_bias max : " + str(np.max(self.delta_bias)))
        print("           min : " + str(np.min(self.delta_bias)))


class Convolutionnal:
    """
            CONVOLUTIONNAL
    - size : tuple des dimensions (D, H, W)
    - weights : tableau des poids de taille (D, D1, F, F)
    - delta : tableau des ajustements précedents
    - output : tableau des valeurs en sortie
    - term : tableau des termes d'erreur de chaque sortie
    - speed, moment : vitesse d'apprentissage et inertie
    - hyper : (F, S, P) / F : taille du filtre, S : stride (décalage), P : zero-padding
    > init((D2, F, S, P, (speed, moment, white)), (D1, H1, W1))
    > front : fonction calculant les sorties
    > back : fonction modifiant les paramètres de la couches durant l'entrainement
    """

    ident = 0

    def  __init__(self, parameters, prev_size):
        Convolutionnal.ident += 1
        self.id = "Convolutionnal_n°" + str(Convolutionnal.ident)
        D1, H1, W1 = prev_size
        D2, F, S, P, rate = parameters
        if P == -1 and S == 1 :
            P = int((F - 1)/2)
        self.hyper = F, S, P
        H2 = int(((H1 - F + 2*P) // S) + 1)
        W2 = int(((W1 - F + 2*P) // S) + 1)
        self.size = D2, H2, W2
        self.weigths = np.random.randn(D2, D1, F, F) / sqrt(D1*H1*W1)
        self.delta = np.zeros((D2, D1, F, F))
        self.bias = np.ones((D2)) / sqrt(D1*H1*W1)
        self.delta_bias = np.zeros((D2))
        self.term = np.zeros(self.size)
        self.output = np.zeros(self.size)
        self.speed, self.moment, self.white = rate

    def define(self, next_layer):
        print(self.id + " - " + next_layer.id, end = " : ")
        print(self.size)
        F, S, P = self.hyper
        print("     Weigths : " + str(np.shape(self.weigths)))
        print("     Term : " + str(np.shape(self.term)))
        print("     Output : " + str(np.shape(self.output)))
        print("     Filter : " + str(F))
        print("     Stride : " + str(S))
        print("     Padding : " + str(P))

    def front(self, inp):
        D1, H1, W1 = inp.shape
        D, H, W = self.size
        F, S, P = self.hyper
        padded_inp = np.zeros((D1, H1 + 2*P, W1 + 2*P))
        padded_inp[:, P:H1+P, P:W1+P] = inp
        for h in range(H):
            for w in range(W):
                self.output[:, h, w] = np.sum(np.sum(np.sum(self.weigths * padded_inp[:, h*S:h*S+F, w*S:w*S+F], axis = 3), axis = 2), axis = 1) + self.bias
        # sortie :
        print("\n" + self.id)
        print("    out max : " + str(np.max(self.output)))
        print("        min : " + str(np.min(self.output)))
        print("weigths max : " + str(np.max(self.weigths)))
        print("        min : " + str(np.min(self.weigths)))
        print("   bias max : " + str(np.max(self.bias)))
        print("        min : " + str(np.min(self.bias)))

    def back(self, prev_layer):
        D, H, W = self.size
        D1, H1, W1 = prev_layer.size
        F, S, P = self.hyper
        padded_prev_out = np.zeros((D1, H1 + 2*P, W1 + 2*P))
        padded_prev_out[:, P:H1+P, P:W1+P] = prev_layer.output
        padded_prev_term = np.zeros((D1, H1 + 2*P, W1 + 2*P))

        # biais :
                           # partie inertielle
        self.delta_bias = (self.moment*self.delta_bias)

        # poids :
                      # partie inertielle        # white-decay
        self.delta = (self.moment*self.delta) - (self.white*self.speed*self.weigths)
        for h in range(H):
            for w in range(W):
                    # on envoie le terme d'erreur en le pondérant dans le neurone précedent
                padded_prev_term[:, h*S:h*S+F, w*S:w*S+F] += np.sum(np.transpose(np.transpose(self.term[:, h, w]) * np.transpose(self.weigths)), axis = 0)
                for d in range(D):
                                            # part d'erreur
                    self.delta[d] += (self.speed * padded_prev_out[:, h*S:h*S+F, w*S:w*S+F] * self.term[d, h, w]) / (H*W)
                    self.delta_bias[d] += (self.speed*self.term[d, h, w]) / (H*W)
        prev_layer.term = padded_prev_term[:, P:H1+P, P:W1+P]
        self.weigths += self.delta
        self.bias += self.delta_bias
        # sortie :
        print("\n" + self.id)
        print("      term max : " + str(np.max(self.term)))
        print("           min : " + str(np.min(self.term)))
        print("     delta max : " + str(np.max(self.delta)))
        print("           min : " + str(np.min(self.delta)))
        print("delta_bias max : " + str(np.max(self.delta_bias)))
        print("           min : " + str(np.min(self.delta_bias)))


class Pooling:
    """
            POOLING
    - size : tuple des dimensions (D, H, W)
    - output : tableau des valeurs en sortie
    - term : tableau des termes d'erreur de sortie
    - hyper : (F, S) / F : taille du filtre, S : stride (décalage)
    > init((F, S), (D1, H1, W1))
    > front : fonction calculant les sorties
    > back : fonction modifiant les paramètres de la couches durant l'entrainement
    """
    ident = 0

    def  __init__(self, parameters, prev_size):
        Pooling.ident += 1
        self.id = "Pooling_n°" + str(Pooling.ident)
        D1, H1, W1 = prev_size
        F, S = parameters
        self.hyper = parameters
        H2 = int(((H1 - F) // S) + 1)
        W2 = int(((W1 - F) // S) + 1)
        self.size = D1, H2, W2
        self.term = np.zeros(self.size)
        self.output = np.zeros(self.size)

    def define(self):
        print(self.id, end=' : ')
        print(self.size)

    def front(self, inp):
        D, H, W = self.size
        F, S = self.hyper
        for d in range(D):
            for h in range(H):
                for w in range(W):
                    self.output[d, h, w] = np.max(inp[d, h*S:h*S+F, w*S:w*S+F])
        # sortie :
        print("\n" + self.id)

    def back(self, prev_layer):
        D, H, W = self.size
        F, S = self.hyper
        prev_layer.term = prev_layer.term - prev_layer.term

        for d in range(D):
            for h in range(H):
                for w in range(W):
                    for j in range(h*S, h*S + F):
                        for k in range(w*S, w*S + F):
                            if prev_layer.output[d, j, k] == self.output[d, h, w] :
                                prev_layer.term[d, j, k] += self.term[d, h, w]
        # sortie :
        print("\n" + self.id)


class Sigmoid:

    def  __init__(self, parameters, prev_size):
        self.id = "Sigmoid"
        self.size = prev_size
        self.term = np.zeros(self.size)
        self.output = np.zeros(self.size)
        self.error = 0

    def front(self, inp):
        # sigmoid = lambda x : 1 / (1 + exp(-x))
        def sigmoid(array):
            return 1 / (1 + np.exp(-array))
        self.output = sigmoid(inp)

    def back(self, prev_layer):
        # on adapte le terme d'erreur qui n'est alors que la somme des termes précédents pondérés
        prev_layer.term = self.term * self.output * (1 - self.output)

    def loss(self, expect):
        out = np.copy(np.reshape(self.output, np.shape(expect)))
        err = expect - out
        self.term += np.reshape(err, np.shape(self.term))
        self.error = np.sum(err**2)/2


class Relu:

    def  __init__(self, parameters, prev_size):
        self.id = "ReLU"
        self.size = prev_size
        self.term = np.zeros(self.size)
        self.output = np.zeros(self.size)
        self.error = 0

    def front(self, inp):
        def ReLU(array):
            zero = np.zeros(np.shape(array))
            return np.maximum(zero, array) + 0.01*np.minimum(zero, array)
        self.output = ReLU(inp)

    def back(self, prev_layer):
        # on adapte le terme d'erreur qui n'est alors que la somme des termes précédents pondérés
        M = np.copy(self.output)
        M[M >= 0] = 1
        M[M < 0] = 0.01
        prev_layer.term = self.term * M

    def loss(self, expect):
        out = np.copy(np.reshape(self.output, np.shape(expect)))
        err = expect - out
        self.term += np.reshape(err, np.shape(self.term))
        self.error = np.sum(err**2)/2


class Softmax:
    """
            SOFTMAX
    - size : tuple des dimensions (D, H, W)
    - output : tableau des valeurs en sortie
    - term : tableau des termes d'erreur de chaque sortie
    > init((D2, H2, W2, (speed, moment, white)), (D1, H1, W1))
    > front : fonction calculant les sorties
    > back : fonction modifiant les paramètres de la couches durant l'entrainement
    """
    def  __init__(self, param, prev_size):
        self.id = "Softmax"
        self.size = prev_size
        self.term = np.zeros(self.size)
        self.output = np.zeros(self.size)
        self.error = 0

    def front (self, inp):
        inp -= np.max(inp)
        e = np.exp(inp)
        self.output = e / np.sum(e)

    def back (self, prev_layer):
        prev_layer.term = self.term

    def loss (self, expect):
        out = np.copy(np.reshape(self.output, np.shape(expect)))
        err = expect - out
        self.term += np.reshape(err, np.shape(self.term))
        self.error = - np.sum(expect*np.log(out))



def saveArrays(net):
    if not (net.id + "_save") in os.listdir("."):
        os.mkdir(net.id + "_save")
    for l in net.layers :
        if type(l) == FullyConnected or type(l) == Convolutionnal:
            np.savez_compressed(net.id + "_save/" + l.id, w = l.weigths, d = l.delta, b = l.bias, db = l.delta_bias)


def loadArrays(net):
    for l in net.layers :
        if type(l) == FullyConnected or type(l) == Convolutionnal:
            loaded = np.load(net.id + "_save/" + l.id + ".npz")
            l.weigths = loaded["w"]
            l.delta = loaded["d"]
            l.bias = loaded["b"]
            l.delta_bias = loaded["db"]




class Normal:

    ident = 0

    def __init__(self, rg, param, prev_size):
        self.id = "Normal"
        self.rank = rg
        self.size = prev_size
        self.hyper = param
        self.sum = 0
        self.term = np.zeros(self.size)
        self.output = np.zeros(self.size)

    def define(self):
        print(self.id, end=' : ')
        print(self.size)

    def front(self, inp):
        D, H, W = self.size
        if self.hyper == 0:
            self.norm = np.linalg.norm(inp)
        else:
            self.norm = np.linalg.norm(inp) * ((H*W) / (self.hyper**2))
        self.output = inp / self.norm

    def back(self, prev_layer):
        prev_layer.term = self.term / self.norm






"""
_________________________________________________________________________________________
_________________________________________________________________________________________

                                        TESTS
_________________________________________________________________________________________
_________________________________________________________________________________________

"""


def Exemples():
    lay_list = [(Input, (3, 32, 32)),
                (ConvSigmoid, (4, 5, 1, 0, (1, 0.9))),
                (ConvSigmoid, (5, 5, 1, 0, (1, 0.9))),
                (FullySigmoid, (5, 1, 1, (1, 0.9, 0.0005)))]
    
    cat_list = ["dog", "cat", "car", "boat", "spoon"]
    
    net = Network(lay_list, cat_list)
    net.define()
    return "Done"


def Test_FC():
    d, h, w = 3, 16, 16
    volume = (d, h, w)
    
    lay_list = [(Input, volume),
                (FullyMax, (1, 1, 6, (0.01, 0.3, 0.))),
                (FullyMax, (1, 1, 2, (0.01, 0.3, 0.)))]
    cat_list = [0, 1]
    
    net = Network("Volume", lay_list, cat_list)
    net.define()
    

    img1 = np.ones(volume)
    img2 = np.ones(volume)
    img3 = np.ones(volume)
    img4 = np.ones(volume)
    
    for j in range(d):
    	for i in range(h*w):
    	    img1[j, randint(0, h-1), randint(0, w-1)] = 0.1
    	for i in range(int(h*w*0.75)):
    	    img2[j, randint(0, h-1), randint(0, w-1)] = 0.1
    	for i in range(int(h*w*0.50)):
    	    img3[j, randint(0, h-1), randint(0, w-1)] = 0.1
    	for i in range(int(h*w*0.25)):
    	    img4[j, randint(0, h-1), randint(0, w-1)] = 0.1

    print(img1)
    
    ex1 = (img1, np.array([[[0.1, 0.1]]]))
    ex2 = (img2, np.array([[[0.1, 1]]]))
    ex3 = (img3, np.array([[[1, 0.1]]]))
    ex4 = (img4, np.array([[[1, 1]]]))
    
    setup = []
    for i in range(100):
        setup.append(ex1)
        setup.append(ex2)
        setup.append(ex3)
        setup.append(ex4)

    net.training(setup)
    return "Done"


def Test_Deep_FC():
    lay_list = [(Input, (1, 1, 5)),
    			(FullyConnected, (1, 1, 5, (0.1, 0.9, 0.))), (Sigmoid, 0),
                (FullyConnected, (1, 1, 5, (0.1, 0.9, 0.))), (Sigmoid, 0)]
    
    cat_list = ["0", "1", "2", "3", "4"]
    
    ex1 = (np.array([[[0.1, 1, 1, 1, 0.1]]]), np.array([1, 0.1, 0.1, 1, 0.1]))
    ex2 = (np.array([[[1, 0.1, 0.1, 1, 1]]]), np.array([0.1, 1, 0.1, 0.1, 1]))
    ex3 = (np.array([[[1, 1, 1, 0.1, 1]]]), np.array([0, 1, 1, 0, 1]))
    ex4 = (np.array([[[0.1, 1, 0, 1, 0.1]]]), np.array([0.1, 0.1, 1, 1, 0.1]))
    
    setup = []
    for k in range(1000):
        setup.append(ex1)
        setup.append(ex2)
        setup.append(ex3)
        setup.append(ex4)
    
    net = Network("Test_Deep_FC", lay_list, cat_list)
    net.training("basic_loss", setup)

    net = Network("Test_Deep_FC", lay_list, cat_list)
    return "Done"


def Test_FC_And():
    lay_list = [(Input, (2, 1, 1)), 
                (FullyMax, (1, 1, 1, (0.1, 0.9, 0.0005)))]
    cat_list = ["True", "False"]
    
    ex1 = (np.array([[[0.]], [[0.]]]), np.array([[[0.]]]))
    ex2 = (np.array([[[0.]], [[1.]]]), np.array([[[0.]]]))
    ex3 = (np.array([[[1.]], [[0.]]]), np.array([[[0.]]]))
    ex4 = (np.array([[[1.]], [[1.]]]), np.array([[[1.]]]))
    
    setup = []
    for i in range(400):
        setup.append(ex1)
        setup.append(ex2)
        setup.append(ex3)
        setup.append(ex4)

    net = Network("And", lay_list, cat_list)
    net.training(setup)
    return "Done"


def Test_Conv():
    d, h, w = 3, 16, 16
    volume = (d, h, w)

    lay_list = [(Input, volume),
                (ConvMax, (5, 5, 1, -1, (0.1, 0.9, 0.0005))),
                (Pooling, (2, 2)),
                (FullyMax, (4, 1, 1, (0.1, 0.9, 0.0005)))]
    cat_list = ["True", "False"]
    
    net = Network("Conv_&_Pool", lay_list, cat_list)
    net.define()
    
    img1 = np.zeros(volume)
    img2 = np.zeros(volume)
    img3 = np.zeros(volume)
    img4 = np.zeros(volume)
    
    for j in range(d):
    	for i in range(h*w):
    	    img1[j, randint(0, h-1), randint(0, w-1)] = randint(0, 10)*0.1
    	for i in range(int(h*w*0.75)):
    	    img2[j, randint(0, h-1), randint(0, w-1)] = randint(0, 10)*0.1
    	for i in range(int(h*w*0.50)):
    	    img3[j, randint(0, h-1), randint(0, w-1)] = randint(0, 10)*0.1
    	for i in range(int(h*w*0.25)):
    	    img4[j, randint(0, h-1), randint(0, w-1)] = randint(0, 10)*0.1
    
    ex1 = (img1, np.array([[[0.]], [[1.]], [[0.]], [[0.]]]))
    ex2 = (img2, np.array([[[0.]], [[0.]], [[0.]], [[1.]]]))
    ex3 = (img3, np.array([[[0.]], [[1.]], [[1.]], [[0.]]]))
    ex4 = (img4, np.array([[[1.]], [[1.]], [[0.]], [[1.]]]))
    
    setup = []
    for i in range(100):
    	setup.append(ex1)
    	setup.append(ex2)
    	setup.append(ex3)
    	setup.append(ex4)
    net.training(setup)
    return "Done"


def Test_Deep_Conv():
    lay_list = [(Input, (3, 32, 32)),
                (Convolutionnal, (5, 5, 1, -1, (0.08, 0.9, 0.0005))), (Relu, 0),
                (Pooling, (2, 2)),
                (Convolutionnal, (5, 5, 1, -1, (0.08, 0.9, 0.0005))), (Relu, 0),
                (Pooling, (2, 2)),
                (Convolutionnal, (5, 5, 1, -1, (0.08, 0.9, 0.0005))), (Relu, 0),
                (FullyConnected, (4, 1, 1, (0.08, 0.9, 0.0005))), (Softmax, 0)]
    cat_list = ["chien", "chat", "pelle", "table"]

    d, h, w = 3, 32, 32
    volume = (d, h, w)
    
    img1 = np.random.randint(0, 255, volume)
    img2 = np.random.randint(0, 255, volume)
    img3 = np.random.randint(0, 255, volume)
    img4 = np.random.randint(0, 255, volume)

    ex1 = ((img1 - np.min(img1)) / (np.max(img1) - np.min(img1)), np.array([1., 0., 0., 0.]))
    ex2 = ((img2 - np.min(img2)) / (np.max(img2) - np.min(img2)), np.array([0., 1., 0., 0.]))
    ex3 = ((img3 - np.min(img3)) / (np.max(img3) - np.min(img3)), np.array([0., 0., 1., 0.]))
    ex4 = ((img4 - np.min(img4)) / (np.max(img4) - np.min(img4)), np.array([0., 0., 0., 1.]))
    
    setup = []
    for i in range(100):
    	setup.append(ex1)
    	setup.append(ex2)
    	setup.append(ex3)
    	setup.append(ex4)

    net = Network("Deep_Conv", lay_list, cat_list)
    net.define()
    net.training(setup)

    return "Done"



def The_Grand_Test():
	lay_list = [(Input, (3, 32, 32)),
                (Convolutionnal, (16, 5, 1, -1, (0.01, 0.9, 0.0005))), (Relu, 0),
                (Pooling, (2, 2)),
                (Convolutionnal, (20, 5, 1, -1, (0.01, 0.9, 0.0005))), (Relu, 0),
                (Pooling, (2, 2)),
                (Convolutionnal, (20, 5, 1, -1, (0.01, 0.9, 0.0005))), (Relu, 0),
                (Pooling, (2, 2)),
                (FullyConnected, (1, 1, 10, (0.01, 0.9, 0.0005))), (Softmax, 0)]

	cat_list = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
	net = Network("The_Grand_Test", lay_list, cat_list)
	net.define()
	net.training_CIFAR(1, (0, 2000), 4)


"""

with open("CIFAR-10/cifar-10-batches-py/data_batch_1", 'rb') as fo:
        	batch = pickle.load(fo, encoding='bytes')
for k in range(10000):
    img = np.zeros((32, 32, 3))
    for d in range(3):
    	for i in range(32):
    			img[i, :, d] = batch[b'data'][k, 1024*d + 32*i : 1024*d + 32*(i+1)]
    expect = np.zeros((10))
    expect[batch[b'labels'][k]] = 1
    ex = (img, expect)
    imsave("Images/img" + str(k) + ".jpg", img)

"""

The_Grand_Test()