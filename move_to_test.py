import os, shutil, random

SOURCE_DIR = "dataset/train"
TEST_DIR   = "dataset/test"
RATIO      = 0.15
SEED       = 42

random.seed(SEED)

for cls in sorted(os.listdir(SOURCE_DIR)):
    cls_src = os.path.join(SOURCE_DIR, cls)
    if not os.path.isdir(cls_src):
        continue
    images = sorted(os.listdir(cls_src))
    random.shuffle(images)
    test_imgs = images[:int(len(images) * RATIO)]
    cls_dst = os.path.join(TEST_DIR, cls)
    os.makedirs(cls_dst, exist_ok=True)
    for img in test_imgs:
        shutil.move(os.path.join(cls_src, img),
                    os.path.join(cls_dst, img))
    print(f"{cls:<22}: {len(test_imgs)} moved to test")

print("\nDone. Run train_ai.py next.")