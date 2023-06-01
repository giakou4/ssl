"""
 ____  _           ____  _                 
/ ___|(_)_ __ ___ / ___|(_) __ _ _ __ ___  
\___ \| | '_ ` _ \\___ \| |/ _` | '_ ` _ \ 
 ___) | | | | | | |___) | | (_| | | | | | |
|____/|_|_| |_| |_|____/|_|\__,_|_| |_| |_|

SimSiam: Exploring Simple Siamese Representation Learning
Link: https://arxiv.org/abs/2011.10566
"""

import torch
from torch import nn
import torch.nn.functional as F 


__all__ = ['SimSiam']


def negative_cosine_similarity(q, z):
    """ Negative Cosine Similarity """
    z = z.detach()
    q = F.normalize(q, dim=1)
    z = F.normalize(z, dim=1)
    return -(q*z).sum(dim=1).mean()
    

class Projector(nn.Module):
    """ Projection Head """
    def __init__(self, in_dim, hidden_dim=2048, out_dim=2048):
        super().__init__()

        self.layer1 = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True)
        )
        self.layer2 = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True)
        )
        self.layer3 = nn.Sequential(
            nn.Linear(hidden_dim, out_dim),
            nn.BatchNorm1d(hidden_dim)
        )

    def forward(self, x):
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        return x 


class Predictor(nn.Module):
    """ Predictor """
    def __init__(self, in_dim=2048, hidden_dim=512, out_dim=2048):
        super().__init__()
        
        self.layer1 = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True)
        )
        self.layer2 = nn.Linear(hidden_dim, out_dim)

    def forward(self, x):
        x = self.layer1(x)
        x = self.layer2(x)
        return x 


class SimSiam(nn.Module):
    """ Contrastive Learning: SimSiam """
    def __init__(self, backbone, feature_size):
        super().__init__()
        
        assert backbone is not None and feature_size>0
        
        self.backbone = backbone
        self.projector = Projector(feature_size, hidden_dim=2048, out_dim=2048)
        self.predictor = Predictor(in_dim=2048, hidden_dim=512, out_dim=2048)
        self.encoder = nn.Sequential(self.backbone, self.projector)
        
    def forward(self, x1, x2):
        f, h = self.encoder, self.predictor
        z1, z2 = f(x1), f(x2) # encoding
        q1, q2 = h(z1), h(z2) # predictor
        loss = negative_cosine_similarity(q1, z2) / 2 + negative_cosine_similarity(q2, z1) / 2 # symmetrical losses
        return loss


if __name__ == '__main__':
    from networks import model_dict
    model_fun, feature_size = model_dict['resnet18']
    backbone = model_fun()
    
    model = SimSiam(backbone, feature_size)
    
    images1 = images2 = torch.rand(4, 3, 224, 224)
    with torch.no_grad():
        loss = model.forward(images1, images2)
        print(f'loss = {loss}')
