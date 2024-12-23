import json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from nltk_utils import bag_of_words, stem, vietnamese_tokenizer
from model import NeuralNet

with open('../resources/Intents.json', 'r') as f:
  intents = json.load(f)
with open('../resources/Questions.json', 'r') as f:
  questions_data = json.load(f)


all_words = []
tags = []
xy = []
for intent in intents['intents']:
  tag = intent['tag']
  tags.append(tag)
  for pattern in intent['patterns']:
    w = vietnamese_tokenizer(pattern)
    all_words.extend(w)
    xy.append((w,tag))
for question_set in questions_data['questions']:
  tag = question_set['tag']
  tags.append(tag)
  for question_answer in question_set['questions_and_answers']:
    if isinstance(question_answer['question'], list):
      for question in question_answer['question']:
        w = vietnamese_tokenizer(question)
        all_words.extend(w)
        xy.append((w, tag))
    else:
      question = question_answer['question']
      w = vietnamese_tokenizer(question)
      all_words.extend(w)
      xy.append((w, tag))
      
ignore_words = ['?', '.', ',', '❤']
all_words = [stem(w) for w in all_words if w not in ignore_words]
all_words = sorted(set(all_words)) 
tags = sorted(set(tags))
  
X_train = []
Y_train =[]
for (pattern_sentence, tag) in xy:
  bag = bag_of_words(pattern_sentence, all_words)
  X_train.append(bag)
  
  label = tags.index(tag)
  Y_train.append(label)
  
X_train = np.array(X_train)
Y_train = np.array(Y_train)

class ChatDataset(Dataset):
  def __init__(self):
    self.n_samples = len(X_train)
    self.x_data = X_train
    self.y_data = Y_train
    
  #dataset[idx]
  def __getitem__(self, index):
    return self.x_data[index], self.y_data[index]
  
  def __len__(self):
    return self.n_samples
  
batch_size = 8 
hidden_size = 8 
output_size = len(tags)
input_size = len(X_train[0])
print(input_size, len(all_words))
print(output_size, tags)
learning_rate = 0.001
num_epochs = 100
  
dataset = ChatDataset()
train_loader = DataLoader(dataset = dataset, batch_size = batch_size, shuffle = True, num_workers = 0)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = NeuralNet(input_size, hidden_size, output_size).to(device)

# loss and optimizer 
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

for epoch in range(num_epochs):
    correct = 0
    total = 0
    running_loss = 0.0  
    for (words, labels) in train_loader:
        words = words.to(device)
        labels = labels.to(device)

        outputs = model(words)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

  
    accuracy = 100 * correct / total
    print(f'Epoch [{epoch + 1}/{num_epochs}], Loss: {running_loss / len(train_loader):.4f}, Accuracy: {accuracy:.2f}%')
    
print(f'Final Loss: {loss.item():.4f}')


data = {
  "model_state": model.state_dict(),
  "input_size": input_size,
  "output_size": output_size,
  "hidden_size": hidden_size,
  "all_words": all_words, 
  "tags": tags
}

FILE = "data.pth"
torch.save(data,FILE) 

print(f'Hoàn thành training. Lưu file vào {FILE}')