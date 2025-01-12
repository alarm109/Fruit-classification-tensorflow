import tensorflow as tf
import tensorflow.keras as K
import tensorflow.keras.backend as KBackend
from tensorflow.keras.optimizers import RMSprop, Adam
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from datetime import datetime
import pathlib
from model import create_model, create_model_with_weight
from utils.csv import write_results_to_csv

train_dir = "/Users/matas/Documents/projects/university/Fruit-classification-tensorflow/Training"
test_dir = "/Users/matas/Documents/projects/university/Fruit-classification-tensorflow/Test"
weight_file = "weights_best.hdf5"

epochs = 5
batch_size = 64
label_file = "labels.txt"
image_size = (100, 100)  # width and height of the used images

logdir = "logs/scalars/" + datetime.now().strftime("%Y%m%d-%H%M%S")

with open(label_file, "r") as f:
    labels = [x.strip() for x in f.readlines()]
num_classes = len(labels)


def train(
        model,
        train_data,
        test_data
):
    metric = 'val_accuracy'
    checkpoint = ModelCheckpoint(
        weight_file,
        monitor=metric,
        verbose=1,
        save_best_only=True,
        mode='max'
    )
    tensorboard_callback = K.callbacks.TensorBoard(log_dir=logdir)
    callbacks_list = [checkpoint, tensorboard_callback]
    history = model.fit(
        train_data,
        epochs=epochs,
        validation_data=test_data,
        steps_per_epoch = train_data.n // batch_size,
        validation_steps = test_data.n // batch_size,
        callbacks=[callbacks_list],
    )

    return history


def f1_metric(y_true, y_pred):
    true_positives = KBackend.sum(KBackend.round(KBackend.clip(y_true * y_pred, 0, 1)))
    possible_positives = KBackend.sum(KBackend.round(KBackend.clip(y_true, 0, 1)))
    predicted_positives = KBackend.sum(KBackend.round(KBackend.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + KBackend.epsilon())
    recall = true_positives / (possible_positives + KBackend.epsilon())
    f1_val = 2 * (precision * recall) / (precision + recall + KBackend.epsilon())
    return f1_val


def main():
    model = create_model(num_classes)

    model.compile(
        optimizer=Adam(0.001),
        loss="categorical_crossentropy",
        metrics=[
            tf.keras.metrics.Accuracy(),
            tf.keras.metrics.Recall(),
            tf.keras.metrics.Precision(),
            f1_metric,
            tf.keras.metrics.AUC()
        ]
    )

    train_datagen = ImageDataGenerator(rescale=1/255.0,
                                    rotation_range=20,
                                    horizontal_flip=True,
                                    width_shift_range=0.2,
                                    height_shift_range=0.2,
                                    shear_range=0.3,
                                    zoom_range=0.5,
                                    vertical_flip=True
                                    )
    train_data=train_datagen.flow_from_directory(train_dir,target_size=(100,100),batch_size=batch_size,classes=labels)
    #show_images(train_data)
    test_datagen=ImageDataGenerator(rescale=1/255.0)
    test_data=test_datagen.flow_from_directory(test_dir,target_size=(100,100),batch_size=batch_size,classes=labels)

    train(
        model,
        train_data,
        test_data
    )

    best_model = create_model_with_weight(num_classes, weight_file)
    best_model.compile(
        optimizer=Adam(0.001),
        loss="categorical_crossentropy",
        metrics=[
            tf.keras.metrics.Accuracy(),
            tf.keras.metrics.Recall(),
            tf.keras.metrics.Precision(),
            f1_metric,
            tf.keras.metrics.AUC()
        ]
    )

    results = best_model.evaluate(test_data, verbose=1)
    write_results_to_csv(results, epochs, batch_size)

    print("Test accuracy Non quantized model:", results)


def post_quantization(model):
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    # converter.target_spec.supported_ops = [
    #     tf.lite.OpsSet.TFLITE_BUILTINS,  # enable TensorFlow Lite ops.
    #     tf.lite.OpsSet.SELECT_TF_OPS  # enable TensorFlow ops.
    # ]
    tflite_model = converter.convert()
    tflite_models_dir = pathlib.Path("./tf-lite-models/")
    tflite_models_dir.mkdir(exist_ok=True, parents=True)
    tflite_model_file = tflite_models_dir / "model.tflite"
    tflite_model_file.write_bytes(tflite_model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_quant_model = converter.convert()
    tflite_model_quant_file = tflite_models_dir / "model_quant.tflite"
    tflite_model_quant_file.write_bytes(tflite_quant_model)
    print("Converted model to tflite!!!")
    return str(tflite_model_file), str(tflite_model_quant_file)


def convert():
    model = create_model_with_weight(num_classes, weight_file)

    print("Starting Evaluation of converted models ...")
    test_datagen = ImageDataGenerator(rescale=1 / 255.0)
    test_data = test_datagen.flow_from_directory(test_dir, target_size=image_size, batch_size=batch_size)
    lite_model_path, quantized_model_path = post_quantization(model)
    # print("." * 20 + "Evaluating Lite model" + "." * 20)
    # lite_model_acc = evaluate_lite_model(lite_model_path, test_data)
    # print(f"Lite model has accuracy: {lite_model_acc}")
    # print("." * 20 + "Evaluating Quantized Lite model" + "." * 20)
    # lite_model_acc = evaluate_lite_model(quantized_model_path, test_data)
    # print(f"Quantized Lite model has accuracy: {lite_model_acc}")


if __name__ == "__main__":
    main()
    convert()


