import pandas as pd 
import numpy as np 
import click
from pathlib import Path
import pickle
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error,mean_squared_log_error
import yaml
from dvclive import Live
import matplotlib.pyplot as plt
import os
from src.models.train_model import model_eval
from jinja2 import Template

#class for building features from dataset
class VisualizeScores:
    def __init__(self, trainpath, testpath, modelpath, feat,output_path, reportfig_path,home_dir):

        self.trainpath = trainpath
        self.testpath = testpath 
        self.modelpath = modelpath
        self.features = feat
        self.reportfig_path = reportfig_path
        self.output_path = output_path
        self.home_dir = home_dir

    def read_data(self):
        self.df_train = pd.read_csv(self.trainpath)
        self.df_test = pd.read_csv(self.testpath)
    
    def feature(self):

        self.df_train= self.df_train[self.features]
        self.df_test = self.df_test[self.features]
        self.x_train = self.df_train.drop(columns=['trip_duration'])
        self.y_train = self.df_train['trip_duration']
        self.x_test = self.df_test.drop(columns= ['trip_duration'])
        self.y_test = self.df_test['trip_duration']

    def predict(self):
        self.metrics_dict ={'Model':[], 'Train_RMSE':[], 'Train_RMSPE':[], 'Train_MAE':[] , 'Train_R2SCORE':[],
                            'Test_RMSE':[], 'Test_RMSPE':[], 'Test_MAE':[] , 'Test_R2SCORE':[]}
        for filename in os.listdir(self.modelpath):
            filepath = os.path.join(self.modelpath, filename)
            model = pickle.load(open(filepath, 'rb'))
            train_score = model_eval(model,self.x_train, self.y_train)
            test_score = model_eval(model,self.x_test, self.y_test)

            self.metrics_dict['Model'].append(filename.split('_')[0])
            
            self.metrics_dict['Train_RMSE'] = train_score['Root Mean Square Error']
            self.metrics_dict['Train_RMSPE'] = train_score['Root Mean Square Percentage Error']
            self.metrics_dict['Train_MAE'] = train_score['Mean Absolute Error']
            self.metrics_dict['Train_R2SCORE'] = train_score['R2 Score']

            self.metrics_dict['Test_RMSE'] = test_score['Root Mean Square Error']
            self.metrics_dict['Test_RMSPE'] = test_score['Root Mean Square Percentage Error']
            self.metrics_dict['Test_MAE'] = test_score['Mean Absolute Error']
            self.metrics_dict['Test_R2SCORE'] = test_score['R2 Score']

            
    def visualise_metrics(self):

        self.metrics_df = pd.DataFrame(self.metrics_dict)
        self.metrics_df.set_index('Model', inplace=True)

        ax1 = self.metrics_df[['Train_RMSE', 'Test_RMSE']].plot.bar(title= 'Different models train and test RMSE')
        fig1 = ax1.get_figure()
        fig1.savefig(Path(str(self.reportfig_path) + '\scoring_metrices\Different models train and test RMSE.png'))

        ax2 = self.metrics_df[['Train_RMSPE', 'Test_RMSPE']].plot.bar(title= 'Different models train and test RMSPE')
        fig2 = ax2.get_figure()
        fig2.savefig(Path(str(self.reportfig_path) + '\scoring_metrices\Different models train and test RMSPE.png'))

        ax3 = self.metrics_df[['Train_MAE', 'Test_MAE']].plot.bar(title= 'Different models train and test MAE')
        fig3 = ax3.get_figure()
        fig3.savefig(Path(str(self.reportfig_path) + '\scoring_metrices\Different models train and test MAE.png'))

        ax4 = self.metrics_df[['Train_R2SCORE', 'Test_R2SCORE']].plot.bar(title= 'Different models train and test R2_SCORE')
        fig4 = ax4.get_figure()
        fig4.savefig(Path(str(self.reportfig_path) + '\scoring_metrices\Different models train and test R2_SCORE.png'))

    def report_generator(self):
        
        # Get a list of image files in the folder
        image_folder = Path(str(self.reportfig_path) + '\scoring_metrices')
        image_files = [file for file in os.listdir(image_folder) if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

        # Create an HTML template
        template_str = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <title>Report for different models</title>
        </head>
        <body>
            <h1>Comparative charts for Different scoring metrics of the models</h1>
            {% for image_file in image_files %}
                <div>
                    <img src="{{ image_folder }}\{{ image_file }}" alt="{{ image_file }}">
                    <br>
                </div>
            {% endfor %}
        </body>
        </html>
        """
        template = Template(template_str)

        # Render HTML content
        html_content = template.render(image_folder=image_folder, image_files=image_files)

        # Save HTML content to a file
        report = Path(str(self.home_dir) + '/reports/metrics_report.html')
        
        with open(report, "w") as html_file:
            html_file.write(html_content)

    def metrics_tracker(self):
        self.read_data()
        self.feature()
        self.predict()
        self.visualise_metrics()
        self.report_generator()

        
@click.command()
@click.argument('train_input_filepath', type=click.Path())
@click.argument('test_input_filepath', type=click.Path())
@click.argument('model_path', type=click.Path())
@click.argument('fig_path', type=click.Path())
def main(train_input_filepath,test_input_filepath, model_path,fig_path):

    """ Runs data cleaning and splitting script to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../interim).
    """
    # Set up paths for input and output data
    curr_dir = Path(__file__)
    home_dir = curr_dir.parent.parent.parent
    data_dir = Path(home_dir.as_posix() + '/data')
    output_path = home_dir.as_posix() + '/dvclive'
    train_input_path = Path(data_dir.as_posix() + train_input_filepath)
    test_input_path = Path(data_dir.as_posix() + test_input_filepath)
    model_path  = Path(home_dir.as_posix() + model_path)
    reportfig_path = Path(home_dir.as_posix() + fig_path)
    params_path = Path(home_dir.as_posix()+'/params.yaml')

    #loading parameters of train model from params.yaml file 
    model_params=yaml.safe_load(open(params_path))['train_model']
    features = model_params['features']
    
    mtrcs = VisualizeScores(train_input_path, test_input_path, model_path, features,output_path, reportfig_path,home_dir)

    mtrcs.metrics_tracker()
    
if __name__== "__main__":
    main()
    

