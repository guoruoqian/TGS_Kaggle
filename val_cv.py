from utils.augmentation import BaseTransform, HengBaseTransform
from options.base_options import SegOptions
from dataset.salt_set import SaltSet
from model.base_model import BaseModel
from utils.func import save_img, generate_pred_target_pkl, get_fold_data
import torch.utils.data as data
from tqdm import tqdm
from utils.tta import tta_collate
from torch.utils.data.dataloader import default_collate
import pickle
import os


if __name__ == '__main__':
    options = SegOptions()
    args = options.parse()
    options.setup_option()

    MEAN = [104.00698793, 116.66876762, 122.67891434]

    save_name = '{}_{}.pkl'
    val = pickle.load(
        open(os.path.join(args.data_root, 'kfold{}/'.format(args.total_fold), save_name.format('val', args.fold_index)), 'rb'))
    print(val['names'][0:5], 'val', 'using {}/{} fold'.format(args.fold_index, args.total_fold))

    # train_val = pickle.load(open(os.path.join(args.data_root, 'train_val.pkl'), 'rb'))
    # train, val = get_fold_data(args.fold_index, args.total_fold, train_val)

    image_root = os.path.join(args.data_root, 'train', 'images')

    if args.aug == 'heng':
        base_aug = HengBaseTransform(MEAN)
    elif args.aug == 'default':
        base_aug = BaseTransform(args.size, MEAN, None)
    else:
        raise NotImplemented

    val_dataset = SaltSet(val, image_root, base_aug, use_depth=args.use_depth, original_mask=True)
    # val_dataset = SaltSet(val, image_root, VOCBaseTransform(MEAN, args.size, args.size, 0), args.use_depth, original_mask=True)
    val_dataloader = data.DataLoader(val_dataset, batch_size=args.batch_size, num_workers=args.num_workers,
                                     pin_memory=True, collate_fn=tta_collate if args.use_tta else default_collate,
                                     shuffle=False)

    model = BaseModel(args)
    model.init_model()
    model.load_trained_model()

    pred, true = model.test_val(val_dataloader)

    # pred_all = np.argmax(np.array(pred), 1)  #(N, 128, 128)
    # target_all = np.array(true).astype(np.int) # (N, 128, 128)
    # generate_pred_target_pkl(pred_all, target_all)

    if args.vis:
        print('vis mask ...')
        OUT_1 = os.path.join('Visualize', args.exp_name + '_pred')
        OUT_2 = os.path.join('Visualize', args.exp_name + '_mask')
        if not os.path.exists(OUT_1):
            os.makedirs(OUT_1)
        if not os.path.exists(OUT_2):
            os.makedirs(OUT_2)

        for i, d in tqdm(enumerate(val['names'])):
            name = d
            tmp = pred[i]
            save_img(tmp > 0.5, os.path.join(OUT_1, name + '_pred.jpg'))
            tmp = true[i]
            save_img(tmp, os.path.join(OUT_2, name + '_true.jpg'))










