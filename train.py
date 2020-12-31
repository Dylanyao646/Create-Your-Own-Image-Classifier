import torch
from torch import nn
from torch import optim
import torch.nn.functional as F
from torchvision import datasets, transforms, models
import numpy as np
from PIL import Image
# import argparse
import argparse
import sys
# parser.add_arguement(--'', type= , default='', help='')

# define command line arguments 
parser = argparse.ArgumentParser()
parser.add_argument('--sav_dir', type=str, default='save_directory', help='Directory to save checkpoint')
parser.add_argument('--arch', type=str, default='vgg13')
parser.add_argument('--lr', type=float, default=0.01, help='enter learning rate')
parser.add_argument('--hidden_units', type=int, default=512, help='enter # of hidden units')
parser.add_argument('--epochs', type=int, default=20, help='enter number of epochs')
parser.add_argument('--gpu_cpu', type=str, default='cuda', help='specify cuda or cpu')
args = parser.parse_args()

# Model hyperparameters
# assign parameters to passed arguments
in_args = parser.parse_args()
learning_rate = in_args.lr
hidden_units = in_args.hidden_units
epochs = in_args.epochs
gpu_cpu = in_args.gpu_cpu
arch = in_args.arch
sav_dir = in_args.sav_dir

# Set data directory for image data
data_dir = 'flowers'
train_dir = data_dir + '/train'
valid_dir = data_dir + '/valid'
test_dir = data_dir + '/test'

# Define the transforms for the training, validation, and testing sets
train_transforms = transforms.Compose([transforms.RandomRotation(30),
                          transforms.RandomResizedCrop(224),
                          transforms.RandomHorizontalFlip(),
                          transforms.ToTensor(),
                          transforms.Normalize([0.485, 0.456, 0.406],
                                       [0.229, 0.224, 0.225])])
validation_transforms = transforms.Compose([transforms.Resize(225),
                             transforms.CenterCrop(224),
                             transforms.ToTensor(),
                             transforms.Normalize([0.485, 0.456, 0.406],
                                          [0.229, 0.224, 0.225])])
test_transforms = transforms.Compose([transforms.Resize(225),
                         transforms.CenterCrop(224),
                         transforms.ToTensor(),
                         transforms.Normalize([0.485, 0.456, 0.406],
                                      [0.229, 0.224, 0.225])])
# Load the datasets with ImageFolder
train_data = datasets.ImageFolder(data_dir + '/train', transform = train_transforms)
validation_data = datasets.ImageFolder(data_dir + '/valid', transform = validation_transforms)
test_data = datasets.ImageFolder(data_dir + '/test', transform = test_transforms)

# Using the image datasets and the trainforms, define the dataloaders
trainloader = torch.utils.data.DataLoader(train_data, batch_size = 64, shuffle = True)
validationloader = torch.utils.data.DataLoader(validation_data, batch_size = 64)
testloader = torch.utils.data.DataLoader(test_data, batch_size = 64)

# image_datasets is a dictionary which has train, validation and test datasets(with transforms)
image_datasets = {
    'train':datasets.ImageFolder(data_dir + '/train', transform = train_transforms),
    'validation':datasets.ImageFolder(data_dir + '/valid', transform = validation_transforms),
    'test':datasets.ImageFolder(data_dir + '/test', transform = test_transforms)
}

# Import JSON file for category mapping
import json
with open('cat_to_name.json', 'r') as f:
    cat_to_name = json.load(f)

# Build and train the network
# Use GPU if it's available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# BUILD THE MODEL
model = models.vgg13(pretrained = True)
model

#Freeze parameters so we don't backprop through them
for param in model.parameters():
    param.requires_grad = False
    
# Define new classifer
classifier = nn.Sequential(nn.Linear(25088, 1000),
                           nn.ReLU(),
                           nn.Dropout(p=0.2),
                           nn.Linear(1000, 102),
                           nn.LogSoftmax(dim=1))

# Set the classifier part of the VGG model = classifier
model.classifier = classifier
criterion = nn.NLLLoss()

# Only train the classifier parameters, feature parameters are frozen
# Optimizers require the parameters to optimize and a learning rate
optimizer = optim.Adam(model.classifier.parameters(), lr=0.01)
#Move this model to available device
model.to(device);

# TRAIN THE MODEL

# Tracking the train steps
steps = 0
# Tracking the loss
running_loss = 0
# How many steps we're going to go before printing out the validation loss
print_every = 40

for epoch in range(epochs):
    # Training loop
    for images, labels in trainloader:
        steps += 1
        
        #move images and labels to GPU
        images, labels = images.to(device), labels.to(device)
        # We need to zero the gradients on each training pass or we'll retain gradients from previous training batches.
        optimizer.zero_grad()
        # Forward pass,  get our logits
        logps = model(images)
        # Calculate the loss with the logits and the labels
        loss = criterion(logps, labels)
        #then backward pass, then update weights
        loss.backward()
        # Take an update step and update the new weights
        optimizer.step()
        
        running_loss += loss.item()
        # STEP 3 Validation loop
        if steps % print_every == 0:
            # turn the model into evaluation mode (turn off dropout)
            model.eval()
            validation_loss = 0
            accuracy = 0
            # Turn off gradients for validation, saves memory and computations
            with torch.no_grad():
                for images, labels in validationloader:
                
                    images, labels = images.to(device), labels.to(device)
                
                    logps = model(images)
                    loss = criterion(logps, labels)
                    validation_loss += loss.item()
                
                    # Calculate the accuracy
                    ps = torch.exp(logps)
                    top_ps, top_class = ps.topk(1, dim=1)
                    equality = top_class == labels.view(*top_class.shape)
                    # Calculate accuracy from equality
                    accuracy += torch.mean(equality.type(torch.FloatTensor))
             
            print(f"Epoch {epoch+1}/{epochs}.."
                  f"Train loss: {running_loss/print_every:.3f}.."
                  f"Validation loss: {validation_loss/len(validationloader): .3f}.."
                  f"Validation accuracy: {accuracy/len(validationloader):.3f}")
            
            running_loss = 0
            model.train()
  
# TODO: Do validation on the test set

# Tracking the train steps
steps = 0
# Tracking the loss
running_loss = 0
# How many steps we're going to go before printing out the validation loss
print_every = 5

for epoch in range(epochs):
    # Training loop
    for images, labels in testloader:
        steps += 1
        
        #move images and labels to GPU
        images, labels = images.to(device), labels.to(device)
        # We need to zero the gradients on each training pass or we'll retain gradients from previous training batches.
        optimizer.zero_grad()
        # Forward pass,  get our logits
        logps = model(images)
        # Calculate the loss with the logits and the labels
        loss = criterion(logps, labels)
        #then backward pass, then update weights
        loss.backward()
        # Take an update step and update the new weights
        optimizer.step()
        
        running_loss += loss.item()
        # Validation loop on the test data
        if steps % print_every == 0:
            # turn the model into evaluation mode (turn off dropout)
            model.eval()
            validation_loss = 0
            accuracy = 0
            # Turn off gradients for validation, saves memory and computations
            with torch.no_grad():
                for images, labels in testloader:
                
                    images, labels = images.to(device), labels.to(device)
                
                    logps = model(images)
                    loss = criterion(logps, labels)
                    validation_loss += loss.item()
                
                    # Calculate the accuracy
                    ps = torch.exp(logps)
                    top_ps, top_class = ps.topk(1, dim=1)
                    equality = top_class == labels.view(*top_class.shape)
                    # Calculate accuracy from equality
                    accuracy += torch.mean(equality.type(torch.FloatTensor))
             
            print(f"Epoch {epoch+1}/{epochs}.."
                  f"Train loss: {running_loss/print_every:.3f}.."
                  f"Validation loss: {validation_loss/len(testloader): .3f}.."
                  f"Validation accuracy: {accuracy/len(testloader):.3f}")
            
            running_loss = 0
            model.train()
# Save the checkpoint 
# The parameters for PyTorch networks are stored in a model's state_dict. 
# And the state dict contains the weight and bias matrices for each of the layers.
model.class_to_idx = image_datasets['train'].class_to_idx
checkpoint = {'arch': 'vgg13',
              'epochs': epochs,
              'state_dict': model.state_dict(),
              'class_to_idx': model.class_to_idx,
              'optimizer_dict': optimizer.state_dict(),
              'input_size': 25088,
              'output_size': 102,
              'classifier' : classifier,
              'learning_rate': 0.01,
             }


torch.save(checkpoint,'checkpoint.pth')
optimizer.state_dict      
