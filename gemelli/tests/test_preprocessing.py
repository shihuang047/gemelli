import unittest
import numpy as np
import pandas as pd
import numpy.testing as npt
from skbio.stats.composition import clr
from gemelli.preprocessing import build, rclr, rclr_matrix


class Testpreprocessing(unittest.TestCase):

    def setUp(self):
        # test dense
        self.count_data_one = np.array([[2, 2, 6],
                                        [4, 4, 2]])
        # test with zeros
        self.count_data_two = np.array([[3, 3, 0],
                                        [0, 4, 2]])
        # test dense tensor
        self.tensor_true = np.array([[[1, 2, 3],
                                      [4, 5, 6]],
                                     [[7, 8, 9],
                                      [10, 11, 12]],
                                     [[13, 14, 15],
                                      [16, 17, 18]]])
        pass

    def test_build(self):

        # flatten tensor into matrix
        matrix_counts = self.tensor_true.transpose([0, 2, 1])
        reshape_shape = matrix_counts.shape
        matrix_counts = matrix_counts.reshape(9, 2)
        # build mapping and table dataframe to rebuild
        mapping = np.array([[0, 0, 0, 1, 1, 1, 2, 2, 2],
                            [0, 1, 2, 0, 1, 2, 0, 1, 2]])
        mapping = pd.DataFrame(mapping.T,
                               columns=['ID', 'conditional'])
        table = pd.DataFrame(matrix_counts.T)
        # rebuild the tensor
        tensor = build()
        with self.assertWarns(Warning):
            tensor.construct(table, mapping,
                             'ID', ['conditional'])
        # ensure rebuild tensor is the same as it started
        npt.assert_allclose(tensor.counts,
                            self.tensor_true.astype(float))
        # test tensor is ordered correctly in every dimension
        self.assertListEqual(tensor.subject_order,
                             list(range(3)))
        self.assertListEqual(tensor.feature_order,
                             list(range(2)))
        self.assertListEqual(tensor.condition_orders[0],
                             list(range(3)))
        # test that flattened matrix has the same clr
        # transform as the tensor rclr
        tensor_clr_true = clr(matrix_counts).reshape(reshape_shape)
        tensor_clr_true = tensor_clr_true.transpose([0, 2, 1])
        npt.assert_allclose(rclr(tensor.counts),
                            tensor_clr_true)

    def test_errors(self):

        # flatten tensor into matrix
        matrix_counts = self.tensor_true.transpose([0, 2, 1])
        matrix_counts = matrix_counts.reshape(9, 2)
        # build mapping and table dataframe to rebuild
        mapping = np.array([[0, 0, 0, 1, 1, 1, 2, 2, 2],
                            [0, 1, 2, 0, 1, 2, 0, 1, 2]])
        mapping = pd.DataFrame(mapping.T,
                               columns=['ID', 'conditional'])
        table = pd.DataFrame(matrix_counts.T)
        # rebuild the tensor
        tensor = build()
        with self.assertWarns(Warning):
            tensor.construct(table, mapping,
                             'ID', ['conditional'])
        # test less than 2D throws ValueError
        with self.assertRaises(ValueError):
            rclr(np.array(range(3)))
        # test negatives throws ValueError
        with self.assertRaises(ValueError):
            rclr(tensor.counts * -1)
        tensor_true_error = self.tensor_true.astype(float)
        tensor_true_error[tensor_true_error <= 10] = np.inf
        # test infs throws ValueError
        with self.assertRaises(ValueError):
            rclr(tensor_true_error)
        tensor_true_error = self.tensor_true.astype(float)
        tensor_true_error[tensor_true_error <= 10] = np.nan
        # test nan(s) throws ValueError
        with self.assertRaises(ValueError):
            rclr(tensor_true_error)
        # test rclr_matrix on already made tensor
        with self.assertRaises(ValueError):
            rclr_matrix(self.tensor_true)
        # test rclr_matrix on negatives
        with self.assertRaises(ValueError):
            rclr_matrix(self.tensor_true * -1)
        # test that missing id in mapping ValueError
        with self.assertRaises(ValueError):
            tensor.construct(table, mapping.drop(['ID'], axis=1),
                             'ID', ['conditional'])
        # test that missing conditional in mapping ValueError
        with self.assertRaises(ValueError):
            tensor.construct(table, mapping.drop(['conditional'], axis=1),
                             'ID', ['conditional'])
        # test negatives throws ValueError
        with self.assertRaises(ValueError):
            tensor.construct(table * -1, mapping,
                             'ID', ['conditional'])
        table_error = table.astype(float)
        table_error[table_error <= 10] = np.inf
        # test infs throws ValueError
        with self.assertRaises(ValueError):
            tensor.construct(table_error, mapping,
                             'ID', ['conditional'])
        table_error = table.astype(float)
        table_error[table_error <= 10] = np.nan
        # test nan(s) throws ValueError
        with self.assertRaises(ValueError):
            tensor.construct(table_error, mapping,
                             'ID', ['conditional'])
        # test adding up counts for repeat samples
        table[9] = table[8] - 1
        mapping.loc[9, ['ID', 'conditional']
                    ] = mapping.loc[8, ['ID', 'conditional']]
        with self.assertWarns(Warning):
            tensor.construct(table, mapping, 'ID', ['conditional'])
        duplicate_tensor_true = self.tensor_true.copy()
        duplicate_tensor_true[2, :, 2] = duplicate_tensor_true[2, :, 2] - 1
        npt.assert_allclose(tensor.counts,
                            duplicate_tensor_true.astype(float))

    def test_matrix_rclr(self):

        # test clr works the same if there are no zeros
        npt.assert_allclose(rclr(self.count_data_one.T).T,
                            clr(self.count_data_one))
        # test a case with zeros
        rclr(self.count_data_two)
        # test negatives throw ValueError
        with self.assertRaises(ValueError):
            rclr(self.tensor_true * -1)
