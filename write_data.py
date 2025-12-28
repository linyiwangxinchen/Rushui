def write_data(fid, para_type, prmtname, para_format, para, varargin=None):
    if para_type == 'single':
        fid.write('%%%s %s  %s %%\n' % (para_type, prmtname, para_format))
        if para_format=='STR':
            fid.write('%s\n' % para)
        else:
            fid.write('%-.6g\n' % para)
        fid.write('%end%\n')
    elif para_type == 'enum':
        fid.write('%%%s %s  %s %%\n' % (para_type, prmtname, para_format))
        if para_format == 'STR':
            fid.write('%s\n' % para)
        else:
            fid.write('%-.6g\n' % para)
        fid.write('%end%\n')
    elif para_type=='array1':
        fid.write('%%%s %s  %s %d %%\n' % (para_type, prmtname, para_format, len(para)))
        for row in para:
            # 将格式化后的字符串写入文件
            fid.write('%-.6g ' % row)
        fid.write('\n')
        fid.write('%end%\n')
    elif para_type=='ComArray':
        # 获取 para 的大小
        para_size_1 = para.shape[0]
        para_size_2 = para.shape[1]
        fid.write(f'%%%s %s  %s %d %d %%\n' % (para_type, prmtname, para_format, para_size_1, para_size_2))
        #fprintf(fid,'alt         beta        mach       alpha        cy1         mz1         cx1         cz1         my1         mx1         cyv         cxv       cyv/cxv       Xcp        Delta    \n')
        if isinstance(varargin, list):  # 如果是列表
            para_title = ''
            for i in range(len(varargin)):
                para_title += f'{varargin[i]}    '
        else:
            para_title = varargin
        fid.write('%s\n' % para_title)
        for i in range(para.shape[0]):
            # 将 para(i, :) 格式化为字符串，使用 %.16g 表示浮点数精度
            formatted_row = ' '.join(['%-.6g ' % val for val in para[i, :]])
            # 将格式化后的字符串写入文件
            fid.write(formatted_row)
            fid.write('\n')
        fid.write('%end%\n')
    elif para_type == 'array2':
        fid.write(f'%%%s %s  %s %d %d %%\n' % (para_type, prmtname, para_format, para.shape[0], para.shape[1]))
        for i in range(para.shape[0]):
            # 将 para(i, :) 格式化为字符串，使用 %.16g 表示浮点数精度
            formatted_row = ' '.join(['%-.6g ' % val for val in para[i, :]])
            # 将格式化后的字符串写入文件
            fid.write(formatted_row)
            fid.write('\n')
        fid.write('%end%\n')
