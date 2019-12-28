from flask import Flask, render_template, request
from collections import deque
import json
import threading
import time
import traceback as trcbck
from PIL import Image
import os
import matplotlib.pyplot as plt
import xlsxwriter
import json

app = Flask(__name__)

global q, satisfied_queries, list_of_errors, num_of_errors, list_of_data, list_of_satisfied
q = deque()
list_of_errors = []
list_of_satisfied = []
list_of_data = []
satisfied_queries, num_of_errors = 0, 0

class Query(object):
    def __init__(self, func, traceback=None, data=dict()):
        self.func = func
        self.kwargs = data
        self.traceback = traceback

    def __repr__(self):
        return str(self.func.__name__) + ' | ' + str(self.kwargs)


class TableRow(object):

    amount = 0

    def __init__(self, run, L, N, TOS, M, TOI, n_o_i, p_g_p, a_c_f, t_c_f, a_c_v, t_c_v, suc_runs=None):
        TableRow.amount += 1
        self.run = int(run)
        self.L = str(L)
        self.N = str(N)
        self.TOS = str(TOS)
        self.M = str(M)
        self.TOI = str(TOI)
        self.n_o_i = str(n_o_i)
        self.p_g_p = str(p_g_p)
        self.a_c_f = str(a_c_f)
        self.t_c_f = str(t_c_f)
        self.a_c_v = str(a_c_v)
        self.t_c_v = str(t_c_v)
        self.sortby = str(L) + str(N) + str(TOS) + str(M) + str(TOI)
        self.suc_runs = suc_runs

    
    def to_list(self):
        return [
            self.L,
            self.N,
            self.TOS,
            self.M,
            self.TOI,
            self.n_o_i,
            self.p_g_p,
            self.a_c_f,
            self.t_c_f,
            self.a_c_v,
            self.t_c_v,
        ]
    
    def __repr__(self):
        return self.sortby
    

    @classmethod
    def from_json(cls, j):
        return cls(j.get('run'), j.get('L'), j.get('N'), j.get('type_of_selection'), 
            j.get('mutation'), j.get('type_of_init'), j.get('n_o_i'), 
            j.get('pol_genes_perc'), j.get('avg_coef_fitness'), 
            j.get('top_coef_fitness'), j.get('avg_coef_variance'), 
            j.get('top_coef_variance'), suc_runs=j.get('suc_runs'))

    
    @staticmethod
    def make_csv_from_all_data(query, filename='all_data', path='data/'):
        global list_of_data
        try:
            workbook = xlsxwriter.Workbook('{}.xlsx'.format(filename))
            worksheet = workbook.add_worksheet()
            row, col = 0, 0
            col_titles_1 = ['#', '#', '#', '#', '#', 'Прогін 1', '', '', '', '', '', 'Прогін 2', '', '', '', '', '', 'Прогін 3', '', '', '', '', '','Прогін 4', '', '', '', '', '','Прогін 5', '', '', '', '', '','Середнє по всіх прогонах', '', '', '', '', '','Найкраще по всіх прогонах', '', '', '', '', '','#' ]
            col_titles_2_1 = ['L', 'N', 'тип', 'Pm', 'Ініціалізація']
            col_titles_2_2 = ['NI', '% поліморфних генів', 'середнє значення коефіцієнта пристосованості в популяції', 'найкраще значення коефіцієнта пристосованості в популяції', '-	значення відхилення середнього значення коефіцієнта пристосованості від оптимального', 'значення відхилення найкращого знайденого розв’язку від оптимального']
            col_titles_2_3 = ['SucRuns']

            for title1, title2 in zip(col_titles_1, col_titles_2_1 + 7 * col_titles_2_2 + col_titles_2_3):
                worksheet.write(row, col, title1)
                worksheet.write(row + 1, col, title2)
                col += 1
            
            list_of_data.sort(key=lambda x: x.sortby)
            sorted_by_shit = []
            temp = []
            prev_shit = ''
            is_first = True
            for item in iter(list_of_data):
                if is_first:
                    prev_shit = item.sortby
                    is_first = False
                if item.sortby == prev_shit:
                    temp.append(item)
                else:
                    temp.sort(key=lambda x: int(x.run))
                    sorted_by_shit.append(temp)
                    temp = list()

                    prev_shit = item.sortby
                    temp.append(item)
            if len(temp) > 0:
                temp.sort(key=lambda x: int(x.run))
                sorted_by_shit.append(temp)
                temp = list()

            row, col = 2, 0

            for start_type in iter(sorted_by_shit):
                for i, item in zip(range(len(start_type)), sorted(start_type, key=lambda x: int(x.run))):
                    item_list = item.to_list()
                    if i == 0:
                        for jtem in iter(item_list):
                            worksheet.write(row, col, jtem)
                            col += 1
                    elif i == 6:
                        for jtem in iter(item_list[5:]):
                            worksheet.write(row, col, jtem)
                            col += 1
                        worksheet.write(row, col, item.suc_runs)
                        col = 0
                        row += 1
                    else:
                        for jtem in iter(item_list[5:]):
                            worksheet.write(row, col, jtem)
                            col += 1



            workbook.close()
            return True
        except Exception as exc:
            query.traceback = ''.join(trcbck.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__))
            return False




def process_query():
    global satisfied_queries, list_of_errors, num_of_errors, q, list_of_satisfied
    while True:
        try:
            # time.sleep(1)
            query = q.popleft()
            res = query.func(query)
            # print(res)
            if res:
                list_of_satisfied.append(query)
                satisfied_queries += 1
            else:
                list_of_errors.append(query)
                num_of_errors += 1
        except IndexError:
            time.sleep(1)
            # print('Queue is empty')


def make_obj(query):
    global list_of_data
    try:
        j = query.kwargs
        list_of_data.append(TableRow.from_json(j))
        return True
    except Exception as exc:
        query.traceback = ''.join(trcbck.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__))
        return False

    


def draw_hist(query):
    try:
        j = query.kwargs
        path_name = 'L={}_N={}_TOS={}_M={}_TOI={}'.format(j.get('L'), j.get('N'), j.get('type_of_selection'), j.get('mutation'), j.get('type_of_init'))
        if not os.path.exists('data/'):
            os.mkdir('data/')
        if not os.path.exists('data/{}/'.format(path_name)):
            os.mkdir('data/{}/'.format(path_name))
        if not os.path.exists('data/{}/{}/'.format(path_name, j.get('run'))):
            os.mkdir('data/{}/{}/'.format(path_name, j.get('run')))
        if not os.path.exists('data/{}/{}/histograms/'.format(path_name, j.get('run'))):
            os.mkdir('data/{}/{}/histograms/'.format(path_name, j.get('run')))

        plt.switch_backend('Agg')
        plt.style.use('bmh')

        if not os.path.exists('data/{}/{}/histograms/Попарні_відстані'.format(path_name, j.get('run'))):
            os.mkdir('data/{}/{}/histograms/Попарні_відстані'.format(path_name, j.get('run')))
        plt.title('Попарні відстані, Iteration: {}'.format(j.get('num_of_iter')))
        plt.xlabel(path_name + '_PGP={}'.format(j.get('pol_genes_perc')))
        plt.bar([int(x) for x in j.get('pair_dist').keys()], [int(x) for x in j.get('pair_dist').values()], color='palevioletred')
        plt.savefig('data/{}/{}/histograms/Попарні_відстані/{}.png'.format(path_name, j.get('run'), j.get('num_of_iter')))
        plt.clf()

        if not os.path.exists('data/{}/{}/histograms/Відстані_Геммінга'.format(path_name, j.get('run'))):
            os.mkdir('data/{}/{}/histograms/Відстані_Геммінга'.format(path_name, j.get('run')))
        plt.title('Відстані Геммінга, Iteration: {}'.format(j.get('num_of_iter')))
        plt.xlabel(path_name + '_PGP={}'.format(j.get('pol_genes_perc')))
        plt.bar([int(x) for x in j.get('hem_dist').keys()], [int(x) for x in j.get('hem_dist').values()], color='cornflowerblue')
        plt.savefig('data/{}/{}/histograms/Відстані_Геммінга/{}.png'.format(path_name, j.get('run'), j.get('num_of_iter')))
        plt.clf()

        if not os.path.exists('data/{}/{}/histograms/Дикий_тип'.format(path_name, j.get('run'))):
            os.mkdir('data/{}/{}/histograms/Дикий_тип'.format(path_name, j.get('run')))
        plt.title('Дикий тип, Iteration: {}'.format(j.get('num_of_iter')))
        plt.xlabel(path_name + '_PGP={}'.format(j.get('pol_genes_perc')))
        plt.bar([int(x) for x in j.get('crazy').keys()], [int(x) for x in j.get('crazy').values()], color='indianred')
        plt.savefig('data/{}/{}/histograms/Дикий_тип/{}.png'.format(path_name, j.get('run'), j.get('num_of_iter')))
        plt.clf()

        return True
    except Exception as exc:
        query.traceback = ''.join(trcbck.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__))
        return False


def make_gif(query):
    try:
        j = query.kwargs
        directory_name = 'L={}_N={}_TOS={}_M={}_TOI={}'.format(j.get('L'), j.get('N'), j.get('type_of_selection'), j.get('mutation'), j.get('type_of_init'))
        type = ['Попарні_відстані', 'Відстані_Геммінга', 'Дикий_тип']
        for t in type:
            file_names = sorted((int(fn[:-4]) for fn in os.listdir('data/{}/{}/histograms/{}'.format(directory_name, j.get('run'), t)) if fn.endswith('.png')))
            images = [Image.open('data/{}/{}/histograms/{}/{}.png'.format(directory_name, j.get('run'),t, fn)) for fn in file_names]
            duration = 10000/len(images) 
            if not os.path.exists('data/{}/{}/gifs/'.format(directory_name, j.get('run'))):
                os.mkdir('data/{}/{}/gifs/'.format(directory_name, j.get('run')))
            images[0].save('data/{}/{}/gifs/{}.gif'.format(directory_name, j.get('run'), t), format='GIF', append_images=images[1:], save_all=True, duration=duration, loop=0)
        return True
    except Exception as exc:
        query.traceback = ''.join(trcbck.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__))
        return False


@app.route('/info')
def errors_page():
    return render_template('info.html', satisfied_queries=satisfied_queries,
                           num_of_errors=num_of_errors, list_of_errors=list_of_errors)


@app.route('/queue')
def queue_page():
    return render_template('queue.html', queue=q)


@app.route('/')
def index_page():
    return render_template('index.html', los=list_of_satisfied)


@app.route('/add_to_queue', methods=['POST', 'GET'])
def add_to_queue():
    names = {
        'c': make_obj,
        'h': draw_hist,
        'a': make_obj,
        't': make_obj,
        'mk_gif': make_gif,
        'mk_xlsx': TableRow.make_csv_from_all_data
    }
    if request.method == 'GET':
        query = dict(request.args)
    elif request.method == 'POST':
        query = dict(request.get_json())
    try:
        if query.get('NAME') in names.keys():
            new_query = Query(names.get(query.get('NAME')), data=query)
            q.append(new_query)
        else:
            print('ADD_TO_QUEUE: NAME arg not found!', str(query))       
    except Exception as exc:
        print(''.join(trcbck.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)))
    return 'ok'




if __name__ == '__main__':
    try:
        ip, port = '127.0.0.1', 8080

        pages = """
        Index:          http://{ip}:{port}/
        Queue of tasks: http://{ip}:{port}/queue
        Errors:         http://{ip}:{port}/info

        """

        print(pages.format(ip=ip, port=port))

        t1 = threading.Thread(target=app.run, args=(ip, port))
        t1.start()
        t2 = threading.Thread(target=process_query, args=())
        t2.start()

        

    except Exception as exc:
        print(''.join(trcbck.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)))
