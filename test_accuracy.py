import torch
import torch.nn as nn
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader

MODEL_PATH = "chess_ai.pth"
TEST_DIR   = "dataset/test"
CLASS_FILE = "class_names.txt"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

with open(CLASS_FILE) as f:
    class_names = [l.strip() for l in f]

model = models.mobilenet_v2(weights=None)
model.classifier[1] = torch.nn.Linear(model.last_channel, len(class_names))
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model.to(DEVICE)
model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

dataset = datasets.ImageFolder(TEST_DIR, transform=transform)
loader  = DataLoader(dataset, batch_size=32, shuffle=False, num_workers=0)
classes = dataset.classes

correct_per_class = {c: 0 for c in classes}
total_per_class   = {c: 0 for c in classes}

print("Evaluating on test set...\n")
with torch.no_grad():
    for images, labels in loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        _, preds = torch.max(model(images), 1)
        for label, pred in zip(labels, preds):
            cls = classes[label.item()]
            total_per_class[cls]   += 1
            correct_per_class[cls] += int(pred.item() == label.item())

print(f"{'Class':<22} {'Correct':>8} {'Total':>8} {'Accuracy':>10}")
print("-" * 52)
total_c = total_t = 0
for cls in classes:
    c = correct_per_class[cls]
    t = total_per_class[cls]
    total_c += c
    total_t += t
    print(f"{cls:<22} {c:>8} {t:>8} {c/t*100:>9.1f}%")
print("-" * 52)
print(f"{'OVERALL':<22} {total_c:>8} {total_t:>8} {total_c/total_t*100:>9.1f}%")
print(f"\nTotal test images: {total_t}")