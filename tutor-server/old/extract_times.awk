BEGIN {
    stable = 0
    locusts = 0
    print "users,success,tries,time,result"
}
/Hatching/ {
    stable = 1
    locusts += $7
}
/Practice: succeeded/ && stable == 1 {
#    print locusts ",true," $7"," $9
    if ($7 < 7)
    {
        print locusts ",true," $7 "," $9 ",success"
    }
    else
    {
        print locusts ",false," $7"," $9 ",fail"
    }
}
/Practice: failed/ && stable == 1 {
        print locusts ",false," $7"," $9 ",fail"
    }
