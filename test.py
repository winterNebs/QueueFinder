
def checkbag(actual):
    bag = 0
    bagcounter = [0, 0, 0, 0, 0, 0, 0, 0]
    pmap = ["?", "z", "s", "t", "j", "l", "o", "i"]
    for i in actual:

        if bag % 7 == 0:
            ok = True
            for j in range(7):
                if bagcounter[j + 1] != 1:
                    print(pmap[j+1], " at ", bagcounter[j + 1])
                    ok = False
            if not ok:
                print("BAG ERROR AT ", bag)
            for j in range(len(bagcounter)):
                bagcounter[j] = 0
        bagcounter[pmap.index(i)] += 1
        bag += 1


checkbag(list(input("enterq")))
