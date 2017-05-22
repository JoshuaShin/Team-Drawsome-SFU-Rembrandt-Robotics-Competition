from image_processing.image_processing import process_img
import os

def main():

    # TODO: Implement GUI and run it here

    # Replace this accordingly
    TEST_PICS_DIRECTORY = 'pics/'

    if not os.path.exists(TEST_PICS_DIRECTORY):
        os.makedirs(TEST_PICS_DIRECTORY)

    test_pics = os.listdir(TEST_PICS_DIRECTORY)
    if len(test_pics) == 0:
        print 'No pictures found in directory pics/!'
        return

    img_file = test_pics[0]

    print 'Processing test image', img_file
    process_img(TEST_PICS_DIRECTORY + img_file)

if __name__ == '__main__':
    main()