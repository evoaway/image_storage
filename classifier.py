import torch
import clip
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications.inception_v3 import InceptionV3
from tensorflow.keras.applications.inception_v3 import preprocess_input, decode_predictions
from sklearn.metrics.pairwise import cosine_similarity

keras_model = InceptionV3(weights='imagenet')

device = "cuda" if torch.cuda.is_available() else "cpu"
clip_model, preprocess = clip.load("ViT-B/32", device=device)


def clip_classify(path, classes):
    image = preprocess(Image.open(path)).unsqueeze(0).to(device)
    text = clip.tokenize(classes).to(device)
    with torch.no_grad():
        image_features = clip_model.encode_image(image)
        text_features = clip_model.encode_text(text)

        logits_per_image, logits_per_text = clip_model(image, text)
        probs = logits_per_image.softmax(dim=-1).cpu().numpy()
        class_index = probs.argmax()
    return classes[class_index]


def keras_classify(path):
    image = tf.keras.preprocessing.image.load_img(path, target_size=(299, 299))
    image_array = tf.keras.preprocessing.image.img_to_array(image)
    image_array = tf.expand_dims(image_array, 0)
    image_array = preprocess_input(image_array)

    predictions = keras_model.predict(image_array)
    decoded_predictions = decode_predictions(predictions, top=1)[0]
    result = decoded_predictions[0][1]
    return result
