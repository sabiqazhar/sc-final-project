import base64
import numpy as np
from model.model import Model
from model.preprocessing import Preprocessing
from model.inference import Inference


class Main:
    def __init__(self, img_input):
        self.img_input = img_input
        self.inference()
        self.postpreprocessing()

    def get_model(self):
        model = Model()
        model = model.get_model
        return model

    def prepare_input(self):
        prep = Preprocessing(img_name=self.img_input)
        prep.load_image()
        prep = prep.get_image_
        return prep

    def inference(self):
        model = self.get_model()
        prep = self.prepare_input()
        print(model)
        model = Inference(model, prep)
        self.result = model.infer()

    def postpreprocessing(self):
        dict_map = {
            0:"Angle Boot",
            1:"Bag",
            2:"Coat",
            3:"Dress",
            4:"Pullover",
            5:"Sandals",
            6:"Shirt",
            7:"Sneaker",
            8:"Trouser",
            9:"T-shirt",
            10:"Hat"
        }
        label = dict_map[self.result.tolist()[0]]
        self._label = label

    @property
    def get_results(self):
        return self._label
