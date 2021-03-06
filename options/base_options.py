import os
import torch
import torch.backends.cudnn as cudnn
import argparse
def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")

class SegOptions(object):
    def __init__(self):
        super(SegOptions, self).__init__()
        self.parser = argparse.ArgumentParser()
        self.initialized = False

    def initialize(self):
        # basic opt
        self.parser.add_argument('phase', choices=['train', 'test'], help='choice train or test')
        self.parser.add_argument('exp_name', type=str, help='experiment name')
        self.parser.add_argument('--resume_model', default=None, type=str, help='Resume from image checkpoint')
        self.parser.add_argument('--num_workers', default=4, type=int, help='Number of workers used in dataloading')
        self.parser.add_argument('--start_epoch', default=0, type=int,
                                 help='Begin counting iterations starting from this value (should be used with resume)')
        self.parser.add_argument('--cuda', default=True, type=str2bool, help='Use cuda to train model')
        self.parser.add_argument('--save_folder', default='weights/', help='Location to save checkpoint models')
        self.parser.add_argument('--pretrained', default=True, type=str2bool, help='Whether to use Pretrained model')
        self.parser.add_argument('--data_root', default='/home/grq/data/TGS/')
        self.parser.add_argument('--in_channels', default=3, type=int, help='image channels')

        # train opt
        self.parser.add_argument('--model_name', default='UNet', type=str,
                                 choices=['UNet', 'UNetResNet34', 'UNet11', 'UNetVGG16', 'UNetResNet152', 'deeplab_v2', 'deeplab50_v2', 'deeplab_v3', 'deeplab_v3_plus'], help='image_model')
        self.parser.add_argument('--loss', default='CELoss', type=str,
                                 choices=['DiceLoss', 'CELoss', 'MixLoss', 'LovaszLoss', 'FocalLoss'], help='image_model')
        self.parser.add_argument('--loss_per_img', help='whether compute Lovaszloss per image', action='store_true')
        self.parser.add_argument('--loss_weights', default=[1.0, 1.0], nargs='+', type=float, help='# 0 celoss, # 1 diceloss')
        self.parser.add_argument('--epochs', default=30, type=int, help='Number of training iterations')
        self.parser.add_argument('--stepvalues', default=[18, 25], nargs='+', type=int, help='# of iter to change lr')
        self.parser.add_argument('--lr', '--learning-rate', default=1e-3, type=float, help='initial learning rate')
        self.parser.add_argument('--weight_decay', '--wd', default=5e-4, type=float, help='Weight decay for SGD')
        self.parser.add_argument('--gamma', default=0.5, type=float, help='Gamma update for SGD lr')
        self.parser.add_argument('--momentum', default=0.9, type=float, help='momentum')
        self.parser.add_argument('--batch_size', default=4, type=int, help='Batch size for training')
        self.parser.add_argument('--save_freq', default=5, type=int, help='save weights every # epochs')
        self.parser.add_argument('--size', default=128, type=int, help='resize image size')
        self.parser.add_argument('--vis', help='whether vis', action='store_true')
        self.parser.add_argument('--use_depth', help='whether use depth', action='store_true')
        self.parser.add_argument('--ms', '--multi_scale', help='whether use multi scale', action='store_true')
        self.parser.add_argument('--ms_scales', default=[1.0, 1.25], nargs='+', type=float, help='ms scale')
        self.parser.add_argument('--out_stride', default=16, type=int, help='out stride')
        self.parser.add_argument('--mGPUs', dest='mGPUs',
                            help='whether use multiple GPUs',
                            action='store_true')
        self.parser.add_argument('--lr_policy', default='poly', type=str, choices=['poly', 'step', 'cyclic'])
        self.parser.add_argument('--aug', default='default', type=str, choices=['default', 'heng'])
        self.parser.add_argument('--cyclic_m', help='how many cycles to split', type=int, default=5)
        self.parser.add_argument('--ensemble_exp', default=None, nargs='+', type=str, help='ensemble exp name')
        self.parser.add_argument('--ensemble_model', default=None, nargs='+', type=str, help='ensemble model name')
        self.parser.add_argument('--ensemble_snapshot', default=None, nargs='+', type=str, help='ensemble snapshot name')
        self.parser.add_argument('--ensemble_tta', default=None, nargs='+', type=str2bool, help='ensemble snapshot name')
        self.parser.add_argument('--ensemble_ms', default=None, nargs='+', type=str2bool, help='ensemble snapshot name')
        self.parser.add_argument('--fold_index', default=0, type=int, help='Stratified K-Folds cross-validator # number')
        self.parser.add_argument('--total_fold', default=5, type=int, help='Stratified K-Folds cross-validator # total number')

        # fixed args
        self.parser.add_argument('--num_classes', default=2, type=int, help='# lesion + bg')

        # eval
        self.parser.add_argument('--trained_model', type=str, help='the path of trained model')
        self.parser.add_argument('--use_tta', help='whether use tta', action='store_true')

    def parse(self):
        if not self.initialized:
            self.initialize()
        self.opt = self.parser.parse_args()

        args = vars(self.opt)
        print('--------------Options-------------')
        for k, v in sorted(args.items()):
            print('%s: %s' % (str(k), str(v)))
        print('----------------End---------------')
        return self.opt

    def setup_option(self):
        if self.opt.cuda and torch.cuda.is_available():
            torch.set_default_tensor_type('torch.cuda.FloatTensor')
            cudnn.benchmark = True
        else:
            torch.set_default_tensor_type('torch.FloatTensor')
        # cfg = (v1, v2)[args.version == 'v2']

        if not os.path.exists(self.opt.save_folder):
            os.mkdir(self.opt.save_folder)

        model_save_path = os.path.join(self.opt.save_folder, self.opt.exp_name)
        print('model save path:', model_save_path)
        if (not os.path.exists(model_save_path)) and self.opt.phase == 'train':
            os.mkdir(model_save_path)

