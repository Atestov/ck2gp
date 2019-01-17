from datetime import datetime, date, time

class Person(object):
    def __init__(self, number, name, surn, sex, birt, father = "", mother = "", deat = ""):
        self.number = number
        self.name = name
        self.surn = surn
        self.sex = sex
        self.birt = birt
        self.deat = deat
        self.father = father
        self.mother = mother

    def Show(object):
        return(object.number, object.name, object.surn, object.sex, object.birt +" - "+object.deat)
    
    def hasFather(object):
        return True if object.father != "" else False

    def hasMother(object):
        return True if object.mother != "" else False

# Некоторые функции 

def GCSave(p): #Записывает обьект класса Person в формате Gedcom
    r = "0 @ind"+p.number+"@ INDI\n"+"1 NAME "+p.name+" /"+p.surn+"/\n"+"2 DISPLAY "+p.name+" "+p.surn+"\n" +"2 GIVN "+p.name+"\n" +"2 SURN "+p.surn+"\n"
    r += "1 SEX M\n" if p.sex == "M" else "1 SEX F\n"
       
    r += "1 BIRT\n2 DATE "+p.birt+"\n"
    if p.deat != "":
    	r += "1 DEAT Y\n"+"2 DATE "+p.deat+"\n"
    return(r)
    #Семьи к которым относиться персонаж заполняются позже (во время создания семьи)

def GetValue(line):
    line = line.replace(' ','')
    n = line.find("=")
    if not line[:n] in ['bn', 'fem', 'fat', 'mot', 'dnt', 'b_d', 'd_d']:
    	return (False)
    else:
    	key = line[:n]
    value = line[n+1::]
    if line == 'fem=yes': return ([key,'F']) #Пол персонажа. Если есть fem=yes значит женщина
    if key == 'dnt': return ([key, Fam[value]]) #Династия персонажа
    if value[0] == '"': value = value[1:-1] #Убираем скобочки
    if key == 'bn': return ([key, value]) #Имя персонажа
    while not value[-1].isdigit():
        value = value[:-1]
    return ([key,value])

def GetObjectNumber(line):
	line = line[:line.find('=')]
	line = line.replace(' ','')
	if line.isdigit():
		return (line)
	else:
		return (False)


file = open("Save.ck2","r",encoding = "ISO-8859-1")
line = file.readline()
while line.find('date=')==-1:
    line = file.readline()
line = line.expandtabs(0)
date = line[6:-2]
#Пропустим правила и динамические титулы
for line in file:
    if line.find("dynasties=")!=-1:
        break

Fam = {}
FamNum = ""; FamName = "";
for line in file:
    line = line.expandtabs(0) #Убираем табуляцию файла
    line = line.replace(' ','')
    if line.find("character=")!=-1: #Если фамилии закончились - выходим
        break
    if GetObjectNumber(line): #Если строка с номером династии
        FamNum = GetObjectNumber(line)
    if line.find("name=")!=-1: #Если строка с именем династии
        FamName = line[len("name=\"")+line.find("name=\""):-2]
        Fam[FamNum]=FamName #Тогда добавляем в словарь династий

# Теперь добавим династии существующие на начало игры.
#/home/andrey/Игры/CK2_v3.0/common/dynasties/00_dynasties.txt
f = open("/home/andrey/Игры/CK2_v3.0/common/dynasties/00_dynasties.txt","r",encoding = "ISO-8859-1")
for line in f:
    line = line.expandtabs(0)
    line = line.replace(' ','')
    if GetObjectNumber(line): #Если строка с номером династии
        FamNum = GetObjectNumber(line)
    if line.find("name=")!=-1: #Если строка с именем династии
        FamName = line[len("name=\"")+line.find("name=\""):-2]
        Fam[FamNum]=FamName #Тогда добавляем в словарь династий
f.close()

#Перебор списка персонажей
file.read(2)

ArrPerson = {}
info = {"number":"", "name":"", "surn":"(Lowborn)", "sex":"M","birt":"", "father":"", "mother":"", "deat":""}
Option = {'bn':'name', 'fem':'sex', 'fat':'father', 'mot':'mother', 'dnt':'surn', 'b_d':'birt', 'd_d':'deat'}

line = file.readline()
while not line.find("delayed_event=")!=-1:
    line = line[:-1].expandtabs(0)
    
    if GetObjectNumber(line) != False: # Это номер персонажа
        if info['number'] == "": #Это номер первого персонажа
            info["number"] = GetObjectNumber(line)
        else: # Это номер следующего персонажа
            # Добавим найденную информацию в словарь персонажей
            ArrPerson[info["number"]] = Person(info["number"], info["name"], info["surn"],
                                               info["sex"], info["birt"], info["father"],
                                               info["mother"], info["deat"])
            # Очистим макет с информацией о персонажах
            info = {"number":"", "name":"", "surn":"(Lowborn)", "sex":"M",
                    "birt":"", "father":"", "mother":"", "deat":""}
            info["number"] = GetObjectNumber(line) # И запишем туда новый номер который мы нашли
        line = file.readline()
        continue
    
    parameter = GetValue(line)
    line = file.readline()
    if not parameter:
        continue
    info[Option[parameter[0]]]=parameter[1]
    
file.close()

#Сначала запишем всех персонажей

ListOfPeople = {}
# Список людей. В формате: Информация о персонаже + семьи в которой он состоит.
PeopleNumber = {}
#Ключ - номер в игре, значение номер в файле gedcom

for i in ArrPerson:
        ListOfPeople[ArrPerson[i].number] = GCSave(ArrPerson[i])

# Теперь добавим семьи персонажам.

NumOfNames = {}
# NumOfNames["Номер отца" + "Номер матери"] = *Номер семьи в импортированном файле* 

FamComposition = ['семья 0']
#FamComposition["Номер отца" + "Номер матери"] = состав семьи

for i in ArrPerson:
    p = ArrPerson[i] #p - Person. // Сократим для читаемости кода

    #Если у персонажа нет родителей, пропустим его
    if not (p.hasFather() or p.hasMother()) : continue

    FamNum = p.father + p.mother

    if not FamNum in NumOfNames: #Если такой семьи нет
        NumOfNames[FamNum] = len(NumOfNames)+1
        # Соберем состав семьи в tmp
        tmp = ""; tmp += "0 @fam"+str(NumOfNames[FamNum])+"@ FAM\n"
        tmp += "1 HUSB @ind"+p.father+"@\n" if p.hasFather() else ""
        tmp += "1 WIFE @ind"+p.mother+"@\n" if p.hasMother() else ""
        tmp += "1 CHIL @ind"+p.number+"@\n"
        FamComposition.append(tmp)
        if p.hasFather():
            ListOfPeople[p.father] += "1 FAMS @fam"+str(NumOfNames[FamNum])+"@\n"
        if p.hasMother():
            ListOfPeople[p.mother] += "1 FAMS @fam"+str(NumOfNames[FamNum])+"@\n"

    else: #Такая семья есть. Добавим персонажа как ребенка
    	FamComposition[NumOfNames[FamNum]] += "1 CHIL @ind"+p.number+"@\n"
    #Теперь отметим в информации о персонаже в какой семье он состоит
    ListOfPeople[p.number] += "1 FAMC @fam"+str(NumOfNames[FamNum])+"@\n"
    
# Когда все семьи составленны. Выгрузим их.
f = open("out.ged", "w")
print("0 HEAD\n"+'1 DATE '+date+"\n1 CHAR UTF-8\n1 GEDC\n2 VERS 5.5\n2 FORM LINAGE-LINKED\n", file=f)
for i in ListOfPeople:
    if ListOfPeople[i].find("@fam") != -1:
        print(ListOfPeople[i], file=f)
for i in FamComposition[1::]:
    print(i, file=f)
f.close()
print("Установите дату: " +date)
