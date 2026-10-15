import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
import os

def train_chess_model():
    # SETUP
    # Image preperations (resizing to 224x224, turning into numbers)
    data_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    data_dir = 'dataset/train'

    if not os.path.exists(data_dir):
        print(f"Error: Folder '{data_dir}' not found!")
        print("Please create the folder structure with images first.")
        return

    # Loading the data
    image_dataset = datasets.ImageFolder(data_dir, data_transforms)
    dataloader = torch.utils.data.DataLoader(image_dataset, batch_size=4, shuffle=True)

    class_names = image_dataset.classes
    print(f"Detected Classes: {class_names}")
    print(f"Total Images: {len(image_dataset)}")

    # Loading MobileNetV2
    # Using 'weights='DEFAULT'' to use the pre-trained knowledge
    print("Downloading MobileNetV2...")
    model = models.mobilenet_v2(weights='DEFAULT')

    # 3. Modifying
    # MobileNet's last layer expects multiple classes,
    # Changing it to match our number of chess pieces and the empty square (13 classes).
    num_ftrs = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_ftrs, len(class_names))

    # 4. TRAINING LOOP
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)

    print("Starting Training (This will take time)...")
    model.train() # Set mode to training

    # Looping over the dataset 5 times (Epochs)
    for epoch in range(5):
        running_loss = 0.0
        for inputs, labels in dataloader:
            optimizer.zero_grad()       # Reset gradients
            outputs = model(inputs)     # Guess the piece
            loss = criterion(outputs, labels) # Calculate error
            loss.backward()             # Learn from error
            optimizer.step()            # Update weights

            running_loss += loss.item()

        print(f"Epoch {epoch+1}/5 Complete. Loss: {running_loss:.4f}")

    # 5. SAVING THE TRAINED MODEL
    print("Training Complete! Saving model...")
    torch.save(model.state_dict(), "chess_ai.pth")

    # Saving the class names aswel, so that "0" means "black_bishop"
    with open("class_names.txt", "w") as f:
        for name in class_names:
            f.write(name + "\n")

if __name__ == "__main__":
    train_chess_model()