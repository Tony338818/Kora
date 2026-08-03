import fasttext

model = fasttext.train_supervised(
    input=r"C:\Users\chidu\Desktop\flagship project\app\engine\inventory_model_training.py",
    epoch=50,
    lr=1.0,
    wordNgrams=2
)

model.save_model("app\engine\models\inventory.bin")