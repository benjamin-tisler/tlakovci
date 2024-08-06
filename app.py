import dlx										   # Za negiljotinsko polaganje tlakovcev 
from io import BytesIO
import matplotlib.pyplot as plt

def find_sim(tlk_entr, all_koords, SIRINA, GLOBINA):
	#Poišči tlakovec (isti) na vertikalno simetrični poziciji
	s,v= map(int, tlk_entr[0].split(','))
	yt,xt= tlk_entr[1][0].split("-")
	simx= SIRINA-int(xt)-int(s)	   #print(f"find_sim: {s}x{v} on {xt}-{yt} - {simx}")
	for entr in all_koords:
		if entr[0]==tlk_entr[0]:
			coordx,coordy= entr[1][0].split('-')	 #print(f"{coordx=} {coordy=} {simx=} {entr=} {xt=} {yt=}")
			if simx== int(coordy) and int(yt)==int(coordx):
				return True
	return False

def is_simetric(resitev, dlx_inst, SIRINA, GLOBINA):
	simetric= True
	koords= [(str(dlx_inst.N[rowidx])[2:-1], dlx_inst.getRowList(rowidx)) for rowidx in resitev]	#print (f"before {koords=}")
	koords= sorted(koords, key=lambda k:k[1])	 #print (f"Aftersort {koords=}")
	for j, koord_entry in enumerate(koords):
		found= find_sim( koord_entry, koords, SIRINA, GLOBINA)
		simetric= simetric & found
		if j-1> int(len(resitev)):
			return simetric
	return simetric

def setup_dlx_piece_laying(SIR, GLOB, tlakovci, restr=False):
	rowNames= []; rows = []; OMEJITEV= SIR*GLOB
	if restr=='VERT':
		OMEJITEV+= SIR
	elif restr=='HOR':
		OMEJITEV+= GLOB
	elif restr=='Oboje':
		OMEJITEV*= 2

	for tlakovc in tlakovci:
		st, gt= tlakovc
		for g in range(GLOB-gt+1):		 #vsak tlakovc polagaj po celi površini
			for s in range(int((SIR-st+1)/1)):
				row= []
				for cy in range(g,g+gt):
					for cx in range(s,s+st):
						row+= [cy*SIR+cx]		#zbiraj samo indexe enic 
						#row+= [cy*SIR+SIR-cx]		#zbiraj samo indexe enic 
				if restr=='VERT':
					if s+st<SIR:
						row+= [SIR*GLOB+s+st]
				elif restr=='HOR':
					if g+gt<GLOB:
						row+= [SIR*GLOB+g+gt]
				elif restr=='Oboje':
					#row+= [SIR*GLOB+(g*s)]
					row+= [SIR*GLOB+(g+gt)*(s+st)-1]
				rows+= [row]
				rowNames+= [f"T({st}, {gt})" ]		#future use

	columns= []
	for i in range(OMEJITEV):
		if i<SIR*GLOB:
			columns.append((f"{int(i/SIR)}-{i%SIR}", dlx.DLX.PRIMARY))	  #Omejitev za vsako polje SIRINA*GLOBINA
		else:
			#if restr=='Oboje':
			#	columns.append((f"V{i-SIR*GLOB}", dlx.DLX.PRIMARY))
			#else:
			columns.append((f"V{i-SIR*GLOB}", dlx.DLX.SECONDARY))

	d = dlx.DLX(columns)
	idx_rws= d.appendRows(rows, rowNames)
	return d, idx_rws

def draw_layouts(page_num, constr= False):
	global plts, SIMETRIC
	d, idx_rws= setup_dlx_piece_laying(SIRINA, GLOBINA, tlkvci, constr)

	FIG_WIDTH= 9.3; cap= 15; plot_cols= 3; linecnt= int(cap/plot_cols)
	fgsz= (FIG_WIDTH, linecnt)
	i= 0; skip=int(page_num); mtrxss= set()
	plt.rcParams['figure.max_open_warning'] = 222
	print(f"draw_layouts {page_num=} {constr=} {len(plts)=}")

	fig,ax= plt.subplots(nrows= linecnt, ncols= plot_cols, figsize=fgsz ,squeeze=True)	 #
	rcnt=0
	for rcnt, resitev in enumerate(d.solve() ):	 #for resitev in resitve:  #print(".", end='')
		if not SIMETRIC or is_simetric(resitev, d, SIRINA, GLOBINA):
			skip-= 1
			if skip >0 or (len(plts)>rcnt+1):
				print("s", end='')
				continue

			mtrx= [[0]*SIRINA for _ in range(GLOBINA)]		  #print(f"{i%plot_cols}", end='')
			barva= 1
			for idx_vrstice_resitve in resitev:
				tlakId= d.N[idx_vrstice_resitve]
				for entr in d.getRowList(idx_vrstice_resitve):
					if entr[0] != 'V':
						koords= entr.split('-')
						mtrx[int(koords[0])] [int(koords[1])]= barva
				barva+= 3
			lm= len(mtrxss)
			mtrxss.add(str(mtrx))
			if lm==len(mtrxss): continue

			ax[int(i/plot_cols)][i%plot_cols].axes.xaxis.set_visible(False);		 
			ax[int(i/plot_cols)][i%plot_cols].axes.yaxis.set_visible(False)
			ax[int(i/plot_cols)][i%plot_cols].matshow(mtrx)

			i+= 1; cap-= 1
			if cap<1:
				break
#		elif i%plot_cols==0:
#			print("n", end='')
	if cap>0:
		for yline in range (i%plot_cols, plot_cols):
			fig.delaxes(ax[int(i/plot_cols)][yline])

		for kline in range(int(i/plot_cols)+1, linecnt):
			for x in range(plot_cols):
				try:
					fig.delaxes(ax[kline][x])
				except:
					print(f"{kline}  {x}", end='RR ')
		NO_SOLUTIONS= False

	fig_vis= int(i/plot_cols)
	if fig_vis<7: fig_vis= 7
	fig.set_size_inches(FIG_WIDTH, fig_vis)
	fig.tight_layout()

	if i==0:
		print("Ni rešitve")
		NO_SOLUTIONS= True
		return None
	if int(page_num)-1 == len(plts):
		plts.append(fig)
	print(f"Izčrpanih { rcnt } rešitev, {i} ustreznih. {len(plts)=}, SIZE: {fig_vis} x {FIG_WIDTH}")
	return fig


from flask import Flask, redirect, url_for, request, render_template, Response
from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField, IntegerRangeField, RadioField, StringField
from wtforms.validators import DataRequired
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

app = Flask(__name__)

app.config['SECRET_KEY']= "Skrivnostni ključek"

SIRINA, GLOBINA= 10,3
VERT_C= "Brez"
tlkvci= [ (2,2), (3,2) , (2,3), (1,2), (2,1) ] #, (3,2), (4,3),(3,4) (3,3),
plts= []; NO_SOLUTIONS= False; SIMETRIC=True
 
class DimsForm(FlaskForm):
	S= IntegerRangeField(label='Vertikalnih odsekov', default=10, validators=[DataRequired()] )
	G= IntegerRangeField(label='Horizontalnih odsekov', default=3, validators=[DataRequired()] )
	V_C= RadioField('Omejitve', choices=[('Brez','Brez'),('VERT','Vertikale'),('HOR','Horizontale'),('Oboje','Oboje')], default='Brez')
	SIM= BooleanField(label='Omejitev simetrije', default=True)
	active = BooleanField(default=True)
	submit= SubmitField("Nastavi vrednosti")
	
@app.route('/dims', methods = ['POST', 'GET'])
def dims():
	global SIRINA, GLOBINA, VERT_C, tlkvci, SIMETRIC, plts
	S= None
	G= None
	V_C= None
	SIM= None
	form= DimsForm()

	if form.validate_on_submit():
		S= form.S.data; G= form.G.data; V_C= form.V_C.data; SIM= form.SIM.data
		form.S.data= ''; form.G.data= ''; form.V_C.data= ''; form.active.data= ''; form.SIM.data= ''
		if S!=SIRINA or G!=GLOBINA or VERT_C!=V_C or SIM!=SIMETRIC:
			plts= []
		SIRINA= S; GLOBINA= G; VERT_C= V_C; SIMETRIC= SIM
		
		print(f"VALIDATED: {S=}, {G=}, {V_C=}, {form.active=} {SIM=}")
		dta = dict((key, request.form.getlist(key) if len(request.form.getlist(key)) > 1 \
			else request.form.getlist(key)[0]) for key in request.form.keys())
		print (f"Request data {dta}")
		tmptlk= []
		for idx in dta["active"]:
			tmptlk.append(tlkvci[int(idx)] )
		if len(tlkvci) != len(tmptlk):
			plts= []
		tlkvci= tmptlk
		return redirect('/images/1' )
	else:
		V_C= VERT_C; form.V_C.data= V_C
		SIM=SIMETRIC
		if SIMETRIC:
			form.SIM.data= True
		else:
			form.SIM.data= False
		print(f"INVALID /dims {form.S.data=} {SIRINA=} {form.G.data=} {GLOBINA=} {V_C=} {form.V_C.data=} {VERT_C=}")
		form.S.data= SIRINA; form.G.data= GLOBINA
		return render_template('dims.html', V_C= VERT_C, S=SIRINA, G= GLOBINA, SIM=SIMETRIC,
			form= form, tlakovci=tlkvci, no_solutions=NO_SOLUTIONS )

class PieceForm(FlaskForm):
	NOV= StringField("S, G", validators=[DataRequired()])
	#PCS= SelectField( "Tlakovci", validators=None )
	submit= SubmitField("Dodaj kos")
	submitnew= SubmitField("Dodaj tega in naslednjega")

@app.route('/piece', methods = ['POST', 'GET'])
def piece():
	global tlkvci, plts
	NOV= None
	pform= PieceForm()
	
	if pform.validate_on_submit():
		NOV= pform.NOV.data
		pform.NOV.data= ''
		print(f"{NOV=} {pform} {pform.submitnew}")
		nwe= NOV.split(',')
		for i, ne in enumerate(nwe):
			s= ''
			for chr in ne:
				if chr.isdigit: s= s+chr
			nwe[i]= s
		tlkvci.append( tuple( (int(nwe[0]), int(nwe[1])) ) )
		plts= []
		if pform.submitnew:
			return redirect("/piece")
		return redirect('/images/1' )
	else:
		print(f"INVALID /piece {pform.NOV.data=}")   #{pform.PCS.data=}
		return render_template('piece.html', S= SIRINA, G= GLOBINA, VERT_C=VERT_C, pform= pform, tlakovci=tlkvci, SIM=SIMETRIC )
	
@app.route('/images/<page_num>')
def images(page_num=1):
	global plts, SIRINA, GLOBINA, VERT_C, NO_SOLUTIONS
	print(f"BEFORE: /images/{page_num} {VERT_C=} {len(plts)=} {SIMETRIC=}")
	if page_num:
		if int(page_num)<=1:
			page_num= "1"; nxt= "2"; prv= page_num
		else:
			prv= str(int(page_num)-1); nxt= str(int(page_num)+1)

		print(f"AFTER: /images/{page_num} {prv=} {nxt=} {VERT_C=} {SIMETRIC=}")
		return render_template("images.html", title=page_num, nxt=nxt, \
			prvs=prv, S=SIRINA, G=GLOBINA, V_C=VERT_C, SIM=SIMETRIC, no_solutions=NO_SOLUTIONS)
	else:
		return render_template("images.html", title="1", nxt="2", \
			prvs="1", S=SIRINA, G=GLOBINA, V_C=VERT_C, SIM=SIMETRIC, no_solutions=NO_SOLUTIONS)

@app.route('/fig/<page_num>')
def fig(page_num):
	global plts
	print(f"/fig/ {page_num=} {SIRINA=} {GLOBINA=} {VERT_C=} {tlkvci=} {len(plts)=}")
	if int(page_num)>0 and int(page_num) <= len(plts):
		fig= plts[int(page_num)-1]
		print("CACHE HIT!")
	else:
		fig= draw_layouts(page_num, VERT_C)

	if fig:
		img = BytesIO()
		FigureCanvas(fig).print_png(img)
		return Response(img.getvalue(), mimetype='image/png')
	else :
		return render_template('500.html', S= SIRINA, G= GLOBINA, no_solutions=NO_SOLUTIONS)

@app.errorhandler(404)
def page_not_found(e):
	return render_template("404.html"), 404

@app.errorhandler(500)
def page_not_found(e):
	return render_template("500.html"), 500

if __name__ == '__main__':
   app.run(debug = True)
   