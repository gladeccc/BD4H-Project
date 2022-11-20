import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import numpy as np
import itertools
# TODO: You can use other packages if you want, e.g., Numpy, Scikit-learn, etc.


def plot_learning_curves(train_losses, valid_losses, train_accuracies, valid_accuracies):
	# TODO: Make plots for loss curves and accuracy curves.
	# TODO: You do not have to return the plots.
	# TODO: You can save plots as files by codes here or an interactive way according to your preference.
	plt.plot(train_losses, label='Training Losses')
	plt.plot(valid_losses, label='Validation Losses')
	plt.legend()
	plt.xlabel('epoch')
	plt.ylabel('Loss')
	plt.title('Loss Curve')
	plt.savefig('Loss_Curve.png')
	plt.cla()

	plt.plot(train_accuracies, label='Training f1 Score')
	plt.plot(valid_accuracies, label='Validation f1 Score')
	plt.legend()
	plt.xlabel("epoch")
	plt.ylabel('f1 Score')
	plt.title('f1 Score')
	plt.savefig('f1 Score_Curve.png')
	plt.cla()
	pass


def plot_confusion_matrix(results, class_names):
	# TODO: Make a confusion matrix plot.
	# TODO: You do not have to return the plots.
	# TODO: You can save plots as files by codes here or an interactive way according to your preference.
	CM1 = confusion_matrix(np.array(results)[:, 0], np.array(results)[:, 1])
	CM2=CM1.sum(axis=1)[:,np.newaxis]
	CM2[CM2==0]=1 # in some case the result is 0 for both CM1 and CM2
	CMatrix = CM1 / CM2
	plt.imshow(CMatrix, cmap=plt.cm.Blues)
	plt.title('Normalized Confusion Matrix')
	tick_marks = np.arange(len(class_names))
	plt.xticks(tick_marks, class_names, rotation=30)
	plt.yticks(tick_marks, class_names)
	plt.colorbar()



	for i, j in itertools.product(range(CMatrix.shape[0]), range(CMatrix.shape[1])):
		plt.text(i, j, format(CMatrix[i, j], '.2f'), horizontalalignment='center')

	plt.tight_layout()
	plt.ylabel('True')
	plt.xlabel('Predicted')
	plt.savefig("Confusion.png")
	pass
