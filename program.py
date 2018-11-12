import pandas
import numpy
import matplotlib.pyplot as plt
from typing import Union, List, Any

# import data:

dtype_dict = {'bathrooms': float, 'waterfront': int, 'sqft_above': int, 'sqft_living15': float, 'grade': int,
              'yr_renovated': int, 'price': float, 'bedrooms': float, 'zipcode': str, 'long': float,
              'sqft_lot15': float, 'sqft_living': float, 'floors': float, 'condition': int, 'lat': float, 'date': str,
              'sqft_basement': int, 'yr_built': int, 'id': str, 'sqft_lot': int, 'view': int}

sales = pandas.read_csv('kc_house_data.csv', dtype=dtype_dict)
sales = sales.sort_values(['sqft_living', 'price'])

' <--------------------------- Start of Regression functions ---------------------------> '


def get_numpy_data(data_frame, features_str, output_str):
    data_frame = data_frame.copy()
    data_frame['constant'] = 1  # add a constant column to an SFrame
    # prepend variable 'constant' to the features list
    features_str = ['constant'] + features_str
    # select the columns of data_frame given by the ‘features’ list into the Frame ‘features_frame’
    features_matrix = data_frame[features_str]
    # this will convert the features_frame into a numpy matrix
    features_matrix = numpy.array(features_matrix)
    # assign the column of data_frame associated with the target to the variable ‘output_array’
    output_array = data_frame[output_str]
    # this will convert the Array into a numpy array:
    output_array = numpy.array(output_array).reshape(-1, 1)
    return features_matrix, output_array


def predict_outcome(feature_matrix, weights):
    predictions = numpy.dot(feature_matrix, weights)
    return predictions


def feature_derivative(errors, feature):
    # -2H^T(y-HW)   =>  -2H^T(error)    =>  2 * H^T * error
    feature = 2 * feature
    derivative = numpy.dot(feature, errors)
    return derivative


def regression_gradient_descent(feature_matrix, output, initial_weights, step_size, tolerance):
    """
    Gradient descent **Algorithm**
    :param feature_matrix:
    :param output:
    :param initial_weights: 1×n numpy array
    :param step_size:
    :param tolerance:
    :return:
    """
    converged = False
    weights = numpy.array(initial_weights).reshape(-1, 1)
    while not converged:
        # compute the predictions based on feature_matrix and weights:
        predictions = predict_outcome(feature_matrix, weights)
        # compute the errors as predictions - output:
        errors = output - predictions
        gradient_sum_squares = 0  # initialize the gradient
        # while not converged, update each weight individually:
        for i in range(len(weights)):
            # Recall that feature_matrix[:, i] is the feature column associated with weights[i]
            # compute the derivative for weight[i]:
            derivative = feature_derivative(errors, feature_matrix[:, i])
            # add the squared derivative to the gradient magnitude
            gradient_sum_squares = + derivative ** 2
            # update the weight based on step size and derivative:
            weights[i] = weights[i] + step_size * derivative
        gradient_magnitude = numpy.sqrt(gradient_sum_squares)
        if gradient_magnitude < tolerance:
            converged = True
    return weights


def get_residual_sum_squares(output, predicted_output):
    """
    :param output: price or Y
    :param predicted_output: predicted y or Y_hat
    :return:
    """
    residual = output - predicted_output
    rss = numpy.dot(residual.T, residual)
    return rss


def polynomial_dataframe(feature, degree):
    """
    Generate polynomial features up to degree 'degree'.
    :param feature: Is pandas.Series, float, double type
    :param degree: a number
    :return: data frame to the degree power
    """
    # assume that degree >= 1
    # initialize the data frame:

    poly_dataframe = pandas.DataFrame()
    # and set poly_dataframe['power_1'] equal to the passed feature
    poly_dataframe['power_1'] = feature
    # first check if degree > 1
    if degree > 1:
        # then loop over the remaining degrees:
        for power in range(2, degree + 1):
            # first we'll give the column a name:
            name = 'power_' + str(power)
            # assign poly_dataframe[name] to be feature^power; use apply(*)
            poly_dataframe[name] = feature ** power

    return poly_dataframe


def fit_poly_model(order, train_data, feature: str, valid_data=None, output: str = 'price',
                   l2_penalty=1e-9,
                   normalization: bool = True, model_plot: bool = False, color_scheme: List[str] = None,
                   pause_plotting_time=2):
    """
    It makes a polynomial dataframe by feature to the power of 'order' and plots the feature as x and cost as y, It
    fits the model to the polynomial dataframe using sikit-learn.\n

    :param order:
    :param train_data:
    :param feature:
    :param valid_data:
    :param output:
    :param l2_penalty:
    :param normalization:
    :param model_plot:
    :param color_scheme: a list of color, first entry for scatter points and second for plotting. e.g. ['red', 'blue']
    :param pause_plotting_time:
    :return:
    """
    # an 'order' degree polynomial :
    poly_data = polynomial_dataframe(train_data[feature], order)
    poly_data[output] = train_data[output]

    # compute the regression weights for predicting sales[‘price’]
    #   based on the 1 degree polynomial feature ‘sqft_living’:
    from sklearn.linear_model import Ridge
    # make a new instance of the object:
    model = Ridge(alpha=l2_penalty, normalize=normalization)
    #   convert dataframe to numpy array to prevent shape error with sikit-learn:
    x = numpy.array(poly_data.iloc[:, :-1])
    y = numpy.array(poly_data[output]).reshape(-1, 1)

    model.fit(x, y)

    # store all coefficient in poly1_weights array:
    poly_weights = model.intercept_
    for i in range(0, len(model.coef_)):
        poly_weights = numpy.append(poly_weights, model.coef_[i])

    # Plotting the model, features Xs vs observation Y:
    if model_plot:
        # produce a scatter plot of the training data (just square feet vs price) with fitted model:
        if color_scheme is not None:
            # plot without default color:
            plt.scatter(poly_data['power_1'], poly_data[output], c=color_scheme[0])
            plt.plot(x[:, 0], model.predict(x), c=color_scheme[1])
        else:
            # plot with default color but in different figures:
            import random
            num_figure = random.randint(0, 1000)
            plt.figure(num_figure)
            plt.scatter(poly_data['power_1'], poly_data[output])
            plt.plot(x[:, 0], model.predict(x), c='red')
            plt.figure(num_figure).show()
        plt.pause(pause_plotting_time)

    # compute rss:
    train_rss = get_residual_sum_squares(y, model.predict(x))
    # compute rss on validation set:
    if valid_data is None:
        # Then we don't need validation_rss:
        validation_rss = None
    else:
        poly_data_valid = polynomial_dataframe(valid_data[feature], order)
        poly_data_valid[output] = valid_data[output]

        x_valid = numpy.array(poly_data_valid.iloc[:, :-1])
        y_valid = numpy.array(poly_data_valid[output]).reshape(-1, 1)
        # get ready validation rss to return:
        validation_rss = get_residual_sum_squares(y_valid, model.predict(x_valid))

    return poly_weights, train_rss, validation_rss


' <--------------------------- End of Regression functions ---------------------------> '

# make 15th order sqft_living polynomial:
poly15_sqft_living = polynomial_dataframe(sales['sqft_living'], 15)
# fit a model to the poly sqft_living:
l2_small_penalty = 1.5e-5
from sklearn.linear_model import Ridge

model = Ridge(alpha=l2_small_penalty, normalize=True)
model.fit(poly15_sqft_living, sales['price'])

# 4. Quiz Question: What’s the learned value for the coefficient of feature power_1?
# 1.24873306e+02

# 5. and 6.
# Reading different subset of sales date frame:
set_1 = pandas.read_csv('wk3_kc_house_set_1_data.csv', dtype=dtype_dict)
set_2 = pandas.read_csv('wk3_kc_house_set_2_data.csv', dtype=dtype_dict)
set_3 = pandas.read_csv('wk3_kc_house_set_3_data.csv', dtype=dtype_dict)
set_4 = pandas.read_csv('wk3_kc_house_set_4_data.csv', dtype=dtype_dict)

# 7.
weights_1, _, _ = fit_poly_model(15, set_1, 'sqft_living', model_plot=True)
weights_2, _, _ = fit_poly_model(15, set_2, 'sqft_living', model_plot=True)
weights_3, _, _ = fit_poly_model(15, set_3, 'sqft_living', model_plot=True)
weights_4, _, _ = fit_poly_model(15, set_4, 'sqft_living', model_plot=True)

# 8. Quiz Question: For the models learned in each of these training sets,
#   what are the smallest and largest values you learned for the coefficient of feature power_1?
#   set1: 2.38888336e+04 ,set2: -5.56146435e+04, set3: 4.70987841e+05, set4: -1.45655613e+05




