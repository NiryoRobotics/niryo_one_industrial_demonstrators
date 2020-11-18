
call "%HOMEPATH%\anaconda3\Scripts\activate.bat"
call conda update -n base -c defaults conda
call conda create -n tf_niryo_one tensorflow=2 python=3.6
call conda activate tf_niryo_one
call pip install opencv-python pygame pygame-menu
call pip install --upgrade tensorflow
exit
