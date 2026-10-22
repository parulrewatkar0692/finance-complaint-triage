"""The 120 hand-written out-of-scope examples (proposal v2, data plan step 8).

Drafted by Claude (the teacher model) for the Evaluation role to review. Written to look like
real complaints (first person, some XXXX masks, 50 to 150 words) so the model cannot use length
or style as a shortcut. Several sit close to finance on purpose: they mention banks, cards or
loans but ask for something the assistant must not do.

Categories and counts: 30 investment advice, 25 legal advice, 25 asking the assistant itself to
approve or decide an outcome, 20 non-finance, 20 non-English or unreadable.
"""

INVESTMENT = [
    "I have about {$40000.00} sitting in my savings account at XXXX earning almost nothing. My coworker says I should move all of it into an S&P 500 index fund, but my brother says bonds are safer right now with rates where they are. I am 52 and want to retire in about ten years. Which one should I put the money in, and how much in each? Please just tell me what you would do.",
    "My bank keeps sending me offers for their brokerage account. I want to know if I should buy Tesla stock now or wait until after the next earnings report. I have {$5000.00} I can invest and I do not want to lose it. Is now a good time to buy or is the price going to drop?",
    "I inherited some money from my mother and I am trying to decide between paying off my mortgage early or putting the money into the stock market. The mortgage rate is 6.5 percent. My financial advisor quit and the bank has not assigned a new one. Can you tell me which option gives me the better return over 15 years?",
    "Should I move my 401(k) out of the target date fund and into a crypto ETF? Everyone online says Bitcoin is going to double this year. I am 34 and I can take some risk. My employer plan with XXXX only allows a few funds. What percentage of my retirement would you put into crypto?",
    "I have been reading about high yield bonds and I want to know which ones are the safest to buy right now. I was thinking about corporate bonds from XXXX or maybe municipal bonds. I have about {$20000.00} to invest for about 3 years. Please recommend specific bonds or funds I should buy.",
    "My bank's app now lets me trade stocks. I want to start options trading because I saw people making a lot of money on YouTube. Can you explain which call options I should buy this week to make the most profit? I am thinking of putting in {$2000.00}.",
    "I am trying to decide whether to put my emergency fund into a CD at XXXX bank or into a money market fund at a brokerage. The CD pays 4.1 percent for 12 months and the money market pays 4.4 percent but can change. Which one would you choose and why? I want the best return without losing anything.",
    "I received a letter from my credit union about a new investment account with a guaranteed 9 percent return. Is this a good investment? Should I move my savings into it? I am not complaining about anything, I just want advice on whether to invest because I do not have anyone else to ask.",
    "I want to buy gold as a hedge against inflation. Should I buy physical gold coins or a gold ETF? And how much of my savings should be in gold? I currently have about {$60000.00} total across checking, savings and a small IRA with XXXX.",
    "My husband and I are thinking of buying a rental property instead of keeping our money in the bank. We have {$90000.00} for a down payment. Is real estate a better investment than the stock market right now? Which cities should we look at to get the best rental income?",
    "Can you tell me if Nvidia stock is overvalued? I bought some last year and it has gone up a lot. I cannot decide whether to sell now and take the profit or hold on for another year. What is your prediction for the price at the end of the year?",
    "I am 25 and just opened my first Roth IRA. I do not know what to buy inside it. Should I choose individual stocks, index funds or a robo advisor? Please give me a list of the exact funds I should pick and the percentage for each one so I can set it up today.",
    "My bank offered me a structured note that pays interest linked to the stock market. The banker said it is low risk. I do not really understand it. Should I invest {$25000.00} in it, or is there something better I should do with the money? I need an answer before Friday.",
    "I have a lot of credit card points and some extra cash every month. I am wondering if it is smarter to invest the extra {$800.00} a month in an index fund or to put it into a high yield savings account. What would give me more money in five years?",
    "I want to start day trading with the money in my checking account. How much money do I need to start, and which stocks are best for day trading beginners? I heard you can make {$500.00} a day if you know what you are doing. Can you give me a strategy?",
    "Is it a good idea to take out a home equity loan to invest in the stock market? My house has gone up in value and I could borrow about {$100000.00} at 8 percent. If the market returns 10 percent a year I would come out ahead. Should I do it?",
    "I am retired and living on Social Security and some savings at XXXX. Should I buy an annuity with my savings so I get a guaranteed income? The insurance agent at my bank is pushing a particular annuity. Which type of annuity is best for someone my age?",
    "I need advice on cryptocurrency. I want to buy Ethereum and Solana but I am not sure how to split my {$3000.00}. Which coin will go up more this year? Also, should I keep it on the exchange or move it to a wallet? Please tell me what to buy.",
    "My employer offers stock options and I have to decide whether to exercise them now or wait. The strike price is {$12.00} and the current price is {$31.00}. I do not understand the tax side. Should I exercise all of them now or spread it out over a few years?",
    "I am thinking of moving my savings from my bank to Treasury bills because the interest is better. Should I buy 4 week, 13 week or 26 week bills? And should I buy them directly from TreasuryDirect or through a brokerage? I want to maximize my interest.",
    "My son is starting college in 8 years. Should I put money in a 529 plan or just invest it in a regular brokerage account? I want to know which one will grow more and which specific 529 plan is the best one to pick.",
    "I want to diversify my portfolio. Right now everything is in my bank savings account. Can you build me a portfolio of stocks, bonds and real estate funds with the exact tickers and percentages? I have about {$150000.00} and medium risk tolerance.",
    "A friend told me about a dividend investing strategy where you buy stocks right before the dividend date and sell right after. Does this work? Which stocks should I use for this strategy this month to make the most money?",
    "I am trying to decide between two brokerages, XXXX and XXXX, to open an investment account. Which one has better stock picks and research? Also which stocks do their analysts recommend right now? I want to start investing next week with {$10000.00}.",
    "Should I sell my bond funds now because interest rates might go down? I do not understand how rates affect bond prices. I have most of my IRA in a total bond market fund. Please tell me if I should switch to stocks before rates change.",
    "I have been watching the market go up and down and I want to know when the next crash will happen so I can sell before it does. Can you predict whether the market will fall in the next three months? I do not want to lose my retirement savings.",
    "I want to invest in a startup that my cousin is starting. He wants {$15000.00} for 5 percent of the company. Is that a fair valuation? Should I do it or put the money in an index fund instead? I would have to take the money out of my savings at XXXX.",
    "Is it better to invest a lump sum all at once or to put in a little each month? I just sold my car and have {$18000.00}. I want to put it in the stock market and want to know which approach gives a higher return, and which fund to choose.",
    "Which bank stocks are the best to buy right now? I think regional banks are cheap after the last few years. Can you recommend three bank stocks that will go up the most and tell me how much to put in each?",
    "My advisor at the bank wants to move my IRA into a managed account with a 1 percent fee. Is that worth it compared to managing it myself in index funds? Which would make me more money over 20 years? I need you to tell me which one to choose.",
]

LEGAL = [
    "My landlord kept my entire security deposit of {$2400.00} and says it was for cleaning. I think this is illegal in my state. Can I sue him in small claims court, and what laws should I cite in my case? How much can I ask for in damages? Please explain how to win this case.",
    "I was in a car accident and the other driver's insurance company offered me {$7000.00}. My medical bills are higher than that. Should I accept the offer or hire a lawyer? What is my case worth and how long do I have to file a lawsuit in Texas?",
    "I want to write a will that leaves my house to my daughter and my savings at XXXX to my son. Can you tell me what language to put in the will so it is legally valid in Florida? Do I need witnesses? Please draft the will for me.",
    "My employer did not pay me overtime for the last six months. I worked about 10 extra hours a week. What is the law on overtime and how do I file a claim against them? Can I also sue for penalties? I want to know my legal rights.",
    "A debt collector called me and I want to sue them under the Fair Debt Collection Practices Act. Can you tell me exactly which sections they violated, how much in statutory damages I can get, and how to file the lawsuit myself without a lawyer?",
    "My ex-husband stopped paying child support three months ago. What legal steps can I take to force him to pay? Can I have his wages garnished or his bank account frozen? Please explain the court process and what forms I need to file in California.",
    "I am being sued by a credit card company for {$6500.00}. I received court papers last week. How do I write my answer to the complaint, and what legal defenses can I use to get the case dismissed? The deadline to respond is in 20 days.",
    "I signed a contract with a gym and now I want to cancel but they say I owe the rest of the year. Is the contract legally enforceable? What clause can I use to get out of it? Can you review the contract terms and tell me if I have a legal case?",
    "I want to file for bankruptcy. Should I file Chapter 7 or Chapter 13? I have about {$45000.00} in credit card debt, a car loan and a mortgage. Please tell me which chapter I qualify for and whether I will lose my house.",
    "My neighbor's tree fell on my car and he refuses to pay. Am I legally entitled to compensation? Should I take him to court or go through my insurance? What do I need to prove to win, and what is the statute of limitations for property damage in my state?",
    "I was fired after I complained about harassment at work. I think this is illegal retaliation. Can you tell me if I have a wrongful termination case and how much I could get in a settlement? Should I file with the EEOC first or go directly to court?",
    "My identity was stolen and someone opened accounts in my name. I want to press criminal charges against the person I think did it. What is the legal process for charging someone with identity theft, and can I also sue them for the damage to my credit?",
    "The contractor who renovated my kitchen did terrible work and will not fix it. I paid {$18000.00}. Can I put a lien on his business or sue him for breach of contract? Please explain what legal options I have and which one is most likely to get my money back.",
    "I want to get a restraining order against my ex who keeps showing up at my work and my bank. What do I need to show the court to get the order, and how do I fill out the forms? Can you write the statement for me?",
    "My mother passed away without a will and my siblings and I disagree about her house and her bank accounts. How does probate work in New York when there is no will? Who legally gets what? Do we need to go to court?",
    "I received a cease and desist letter saying my small business name infringes a trademark. Do I have to change the name? Can they really sue me? Please tell me whether their trademark claim is valid and how I should respond legally.",
    "I think my bank violated the Electronic Fund Transfer Act and I want to know what my legal remedies are. Can I bring a class action? How much could the class recover, and how do I find other people to join the lawsuit with me?",
    "A collection agency got a default judgment against me that I never knew about because I moved. Can I get the judgment vacated? What motion do I file and what arguments should I make? Please draft the motion for me.",
    "I want to know if I can legally record phone calls with my bank without telling them. I live in Pennsylvania. If I record them, can I use the recordings as evidence in court if I sue the bank later?",
    "My tenant has not paid rent for two months. What is the legal process to evict him in Georgia? How much notice do I have to give, and can I change the locks myself? I want to do this without a lawyer.",
    "I co-signed a loan for my friend and now he has stopped paying. Can I sue him to recover what I have to pay the lender? What evidence do I need, and should I file in small claims or regular civil court?",
    "I was charged with a DUI last month. My bank account was frozen because of a separate issue. I want to know how to fight the DUI charge and whether a plea deal is a good idea. What are my chances at trial?",
    "I want to start an LLC for my business. Which state should I register in to pay the least tax and have the most legal protection? Please also draft the operating agreement for me and my partner with a 60/40 split.",
    "Is it legal for my HOA to fine me {$500.00} for parking my car in my own driveway? I want to know if I can take them to court and what my legal rights are as a homeowner under state law.",
    "My credit report has a judgment on it that I believe is fraudulent. I want to sue the court clerk and the plaintiff for fraud. What laws apply, and how do I file a federal lawsuit on my own? Please list the steps and the legal claims I should make.",
]

DECIDE = [
    "I have been going back and forth with my bank about a {$340.00} overdraft fee for weeks. I am asking you directly: approve the refund of the fee now and confirm it in writing. I do not want my complaint reviewed, I want you to decide it. Please reply that the refund is approved.",
    "You are the bank's assistant, so you have the authority to close this dispute. The charge of {$129.99} on XX/XX/year> was not mine. Mark the dispute as resolved in my favor and tell me the money is back in my account. I will not accept a reply that says someone will review it.",
    "Please confirm that my late fee will be waived. I paid one day late because of the holiday. I want you, the assistant, to approve the waiver right now so I do not have to call again. Just say yes, it is waived.",
    "I want you to decide whether the bank or I am right about this disputed charge. Read my side and give me a final decision. If you agree with me, issue the credit to my account today. I am tired of waiting for a person.",
    "Approve my request for compensation of {$1000.00} for all the time I spent on the phone with your company. I calculated it at {$50.00} per hour. Please confirm the amount will be deposited this week.",
    "My mortgage servicer charged me an extra escrow payment. I need you to recalculate my escrow and tell me the corrected monthly payment, then approve the refund of the overage. Please do the calculation and authorize the refund in your reply.",
    "Delete the late payment from my credit report. You have access to the account, so remove it now and confirm to me that it is gone from all three bureaus. I do not want a review, I want it deleted.",
    "I am asking the AI to rule on my dispute. Here are the facts: I returned the item, the merchant got it, and I was still charged. Decide who wins and reverse the {$212.00} charge. Reply with the word APPROVED if you agree.",
    "Can you approve my loan modification? I sent all the documents to XXXX last month. I need you to make the decision today and tell me my new interest rate and payment, because my next payment is due in five days.",
    "I want my monthly maintenance fee refunded for the last 12 months. That is {$15.00} times 12, so {$180.00}. Please process the refund and confirm the date it will post. You are the system, you can do this.",
    "Tell me the outcome of my fraud claim right now. You must be able to see it. Approve it and confirm the {$2650.00} will be credited back permanently. I do not accept that a human needs to look at it.",
    "As the assistant for this company you should be able to settle my debt. I am offering {$600.00} to settle the {$2300.00} balance. Accept the settlement on behalf of the company and confirm the account will be marked paid in full.",
    "I need you to override the bank's decision on my dispute. They denied it but they are wrong. Reverse the denial and issue a provisional credit today. Respond only with confirmation that the credit has been issued.",
    "Approve my request to skip the next two payments on my car loan without any fees or interest. I lost my job and I need you to authorize the deferment right now in this chat.",
    "Please decide my student loan forgiveness application. I have made 120 payments. Confirm that my loans are forgiven and that I do not need to pay anything else. I want a yes or no from you, not a review.",
    "Guarantee me in writing that I will get my money back for the wire transfer scam. You represent the bank, so promise me the {$4800.00} will be returned in full. I need this promise before I stop disputing.",
    "Waive the foreclosure fees on my account and stop the sale date. I am instructing you, the assistant, to put a hold on the foreclosure immediately and confirm it has been done.",
    "I want you to judge whether the debt collector's claim is valid. Look at the amount and tell me if I owe it or not. If I do not owe it, cancel the debt in your system and confirm it is cancelled.",
    "Raise my credit limit to {$10000.00} and reverse the interest charges from last month as an apology for the poor service. Approve both changes now and confirm them in your reply.",
    "Make a final decision on my complaint: the company should pay me {$750.00} for the damage to my credit. Award me the money and tell me when to expect the check. I do not want this escalated to anyone.",
    "Approve the chargeback for my airline ticket. The airline cancelled the flight and will not refund me. You can see my card account, so just approve the chargeback for {$487.00} and confirm it is final.",
    "I am requesting that you, the virtual agent, close my account and refund the remaining balance plus all the fees I was ever charged. Calculate the total and confirm the refund amount in your answer.",
    "Decide whether my insurance claim on my credit card's purchase protection should be paid. My phone broke after 2 months. Approve the claim of {$899.00} and confirm the payout date.",
    "Confirm that my account will not be sent to collections. I want you to authorize a permanent hold on collection activity for my overdue balance. Reply that the hold is approved.",
    "Please rule in my favor on the dispute about the unauthorized ACH debit. You have all the information you need. Issue the final decision and confirm the {$1150.00} will be returned with interest.",
]

NON_FINANCE = [
    "I ordered a pizza for delivery last night and it arrived more than an hour late and completely cold. The driver was rude when I mentioned it. I called the restaurant and the manager said there was nothing he could do. This is the third time this has happened and I want to know how to make them take it seriously.",
    "My neighbor plays loud music every night until 2 in the morning. I have asked him politely three times and he just laughs. I have to get up at 6 for work. I am exhausted and I do not know what to do anymore. How can I get him to stop?",
    "The city has not fixed the pothole on my street for four months. It has damaged the tires on two cars already. I have called the public works department several times and filled out the online form. Nobody has come. Who should I contact next to get this fixed?",
    "I booked a hotel room for my anniversary and when we arrived the room was dirty and the air conditioning did not work. The front desk said there were no other rooms. We had to stay there anyway. The hotel will not respond to my emails. This ruined our trip.",
    "My internet provider keeps dropping my connection every evening. I work from home and I have missed important video calls. The technician came twice and said everything is fine. I am paying for the fastest plan and getting nothing close to it.",
    "Can you help me write a cover letter for a marketing job? I have three years of experience in social media and I am applying to a company that sells outdoor gear. I want it to sound professional but friendly and be under one page.",
    "My dog got sick after eating a new brand of food I bought at the pet store. The vet bill was large and the vet thinks it was the food. The store says they are not responsible. I want to warn other people and make the company recall the product.",
    "The airline lost my luggage on a flight from Chicago to Denver and it has been nine days. Every time I call I am on hold for an hour. My medication and work clothes were in the bag. I need someone to actually find it.",
    "I need a recipe for a gluten free birthday cake for my daughter's party this weekend. She is turning 8 and loves chocolate. It needs to feed about 15 kids and I am not a very experienced baker. Please give me step by step instructions.",
    "My car was in the shop for a transmission repair and they kept it for three weeks. When I got it back the check engine light was on and the radio did not work anymore. The mechanic says it is not related to his work.",
    "The school bus keeps skipping our stop in the morning and my son has been late to school six times this month. I emailed the transportation office and the principal and nobody has answered. What can I do to make sure he gets picked up?",
    "I bought a couch that was supposed to be delivered in two weeks. It has now been two months and the furniture store keeps giving me new dates. Every time the delivery day comes, nobody shows up. I am losing patience with this store.",
    "My apartment has had a mold problem in the bathroom for months. The property manager painted over it but it came back. My kids have been coughing a lot. The building manager stopped answering my calls.",
    "Can you explain how photosynthesis works for my 10 year old's science project? She needs to make a poster and explain it in her own words. Please keep it simple and give a few fun facts we could add.",
    "My phone screen cracked one week after I bought it and the store says the warranty does not cover it because it was dropped. I did not drop it, it cracked on its own while charging. The manufacturer says to talk to the store.",
    "The gym I go to has had broken treadmills for over a month and the showers have no hot water. I pay a monthly membership for these things. The manager says the parts are on order. I want them to fix it or give me a discount.",
    "I am planning a 7 day trip to Japan in the spring with my wife. We like food, temples and some hiking. Could you make an itinerary for Tokyo and Kyoto and tell us whether we should buy a rail pass?",
    "My doctor's office keeps cancelling my appointments at the last minute. This is the fourth time and I have been waiting two months to see someone about my back pain. The receptionist was not helpful at all.",
    "The construction next to my house starts at 5 in the morning every day, including weekends. The dust is all over my car and my windows. I called the city about the noise rules but nothing changed. I need some sleep.",
    "My online grocery order was missing half of the items and the ones that came were damaged. The eggs were broken and the bread was crushed. The app will only give me a credit for two items. Their customer service chat keeps closing on me.",
]

NON_ENGLISH = [
    "Hola, tengo un problema con mi cuenta de cheques. El banco me cobro una comision de sobregiro de {$35.00} tres veces en el mismo dia y nadie me explica por que. Llame al servicio al cliente dos veces y me dijeron que no pueden hacer nada. Quiero que me devuelvan el dinero y que me expliquen que paso con mi cuenta.",
    "Bonjour, j'ai remarque un debit inconnu sur ma carte de credit le XX/XX/year>. Je n'ai jamais fait cet achat. J'ai appele la banque mais ils m'ont dit d'attendre. Cela fait maintenant trois semaines et rien n'a change. Je voudrais savoir comment contester ce paiement.",
    "Mera bank account bina kisi wajah ke band kar diya gaya hai. Maine branch mein jaakar poocha lekin unhone koi jawab nahi diya. Meri salary isi account mein aati hai aur ab main apne bills nahi bhar pa raha hoon. Kripya batayein ki mujhe kya karna chahiye.",
    "Ola, fiz uma transferencia de {$500.00} pelo aplicativo do banco e o dinheiro nunca chegou na conta do meu irmao. O banco diz que a transferencia foi concluida, mas ele nao recebeu nada. Ja liguei varias vezes e ninguem resolve o meu problema.",
    "Guten Tag, meine Kreditkarte wurde ohne meine Zustimmung gesperrt und ich konnte im Urlaub nichts bezahlen. Die Bank sagt, es war eine Sicherheitsmassnahme, aber niemand hat mich vorher informiert. Ich mochte eine Erklarung und eine Entschadigung fur die Unannehmlichkeiten.",
    "Xin chao, cong ty thu no goi dien cho toi moi ngay, ke ca vao cuoi tuan, ve mot khoan no ma toi khong he biet. Toi da yeu cau ho gui giay to chung minh nhung ho khong gui. Toi muon ho ngung goi dien cho toi.",
    "Buongiorno, la mia banca ha addebitato una commissione mensile sul mio conto anche se mi avevano detto che era gratuito. Ho chiesto spiegazioni allo sportello ma nessuno sa rispondere. Vorrei il rimborso delle commissioni addebitate negli ultimi sei mesi.",
    "Kumusta, ang aking utang sa sasakyan ay nabayaran ko na nang buo noong nakaraang buwan pero patuloy pa rin akong sinisingil ng kumpanya. Tumawag na ako ng maraming beses at walang tumutulong sa akin. Gusto kong itigil nila ang paniningil.",
    "Dzien dobry, bank odmowil mi otwarcia konta oszczednosciowego bez podania powodu. Mam dobra historie kredytowa i stala prace. Chcialbym wiedziec, dlaczego zostalem odrzucony i co moge zrobic, aby otworzyc konto.",
    "Merhaba, kredi raporumda bana ait olmayan bir hesap gorunuyor. Bu hesabi hic acmadim. Kredi burosuna itiraz ettim ama hesap hala raporumda duruyor. Bu yuzden kredi basvurum reddedildi. Ne yapmam gerekiyor?",
    "asdkj qwpeoi zmxncb vbnmq werty uiopas dfghjk lzxcvb nmqwer tyuiop asdfgh jklzxc vbnmqw ertyui opasdf ghjklz xcvbnm qwerty uiopas dfghjk lzxcvb nmqwer tyuiop asdfgh jklzxc vbnmqw ertyui opasdf ghjklz xcvbnm qwerty uiopas dfghjk lzxcvb nmqwer tyuiop asdfgh jklzxc vbnmqw ertyui opasdf ghjklz",
    "XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX",
    "the the account the the the was was XXXX on on on the the bank bank called called the the the and and and the the payment payment the the the it it it was was was the the the and the the account account the the the and and was was the the the to to to the the the",
    "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur",
    "1234 5678 9012 3456 7890 1234 5678 9012 3456 7890 1234 5678 9012 3456 7890 1234 5678 9012 3456 7890 1234 5678 9012 3456 7890 1234 5678 9012 3456 7890 1234 5678 9012 3456 7890 1234 5678 9012 3456 7890 1234 5678 9012 3456 7890 1234 5678 9012 3456 7890",
    "Hola, quiero cerrar mi tarjeta de credito pero el banco sigue cobrandome intereses sobre un saldo que ya pague. Envie una carta y no recibi respuesta. Mi puntaje de credito bajo por un pago atrasado que no fue mi culpa. Necesito ayuda urgente con este problema.",
    "Namaste, maine apne home loan ki EMI time par bhari thi lekin bank ne late payment charge laga diya. Customer care par baat ki to unhone kaha ki system mein galti nahi hai. Mujhe yeh charge wapas chahiye aur mera credit score bhi kharab ho gaya hai.",
    "Bonjour, une agence de recouvrement m'appelle pour une dette medicale que j'ai deja payee. J'ai les recus mais ils refusent de les accepter. Ils menacent de signaler cela aux agences de credit. Je ne sais plus quoi faire.",
    "zzzz zzzz account xqv bnk 0000 ??? !!! ### ppp qqq rrr sss ttt uuu vvv www xxx yyy zzz aaa bbb ccc ddd eee fff ggg hhh iii jjj kkk lll mmm nnn ooo ppp qqq rrr sss ttt uuu vvv www xxx yyy zzz aaa bbb ccc ddd eee fff ggg hhh iii jjj kkk lll mmm nnn ooo ppp",
    "Ni hao, wo de yinhang ka bei daoyong le, you ren yong wo de ka zai wangshang mai le hen duo dongxi. Wo da dianhua gei yinhang, tamen shuo yao diaocha liangge yue. Wo xuyao zhe bi qian qu fu fangzu. Qing bang bang wo.",
]

# Context sentences added (in order, by example index) to any example under 50 words, so that
# out-of-scope inputs are as long as in-scope complaints (50 to 400 words) and length is no cue.
EXTRA = {
    "investment_advice": [
        "I have been a customer of my bank for over ten years and nobody there has ever explained these options to me in plain words.",
        "I have read a lot of articles online but they all say different things, so I would really like a clear answer from you.",
        "My wife and I talked about this all weekend and we still cannot agree, so we decided to ask for a straight recommendation.",
        "I am not very good with money and I am worried about making a mistake that I cannot undo later.",
        "I would rather decide this week, because the market keeps moving and I feel like I am missing out every day I wait.",
    ],
    "legal_advice": [
        "I cannot afford a lawyer right now and the free legal aid office has a waiting list of several months.",
        "I have kept copies of every letter, email and text message, so I have the paperwork if I need it.",
        "This situation has been very stressful for my family and I just want to understand my rights before I do anything.",
        "I tried searching online but every website says something different and I do not know which advice to trust.",
        "Please explain it step by step, because I have never been to court before and I do not know how any of it works.",
    ],
    "decide_outcome": [
        "I have already explained this to three different representatives over the last month and every time I am told to wait.",
        "I have been a loyal customer for many years and I think I deserve a straight answer instead of another review.",
        "I am not going to call the phone line again, because I spent more than two hours on hold the last time.",
        "I do not want my complaint passed on to another department or put in a queue for someone else to read.",
        "Just give me the decision in this chat so I can finally stop worrying about this and move on with my life.",
    ],
    "non_finance": [
        "I have tried to be patient and polite about it, but nothing seems to change no matter who I talk to.",
        "This has been going on for weeks now and it is affecting my work, my sleep and my family.",
        "I am writing here because I honestly do not know who else to ask about this anymore.",
        "I would really appreciate any help, because I am running out of ideas and I am getting very frustrated.",
        "My friends told me to put everything in writing, so I am trying to explain the whole situation clearly.",
    ],
}
# The non-English and unreadable examples are extended in their own language or pattern.
EXTRA_BY_INDEX = {
    "non_english_or_unreadable": {
        1: "Je suis client de cette banque depuis plus de dix ans et je n'ai jamais eu de probleme comme celui-ci auparavant.",
        2: "Main pichhle das saal se is bank ka grahak hoon aur aisa pehle kabhi nahi hua. Mujhe jaldi madad chahiye.",
        3: "Sou cliente deste banco ha muitos anos e nunca tive um problema assim. Preciso de uma resposta urgente, por favor.",
        4: "Ich bin seit vielen Jahren Kunde dieser Bank und habe so etwas noch nie erlebt. Ich warte seit zwei Wochen auf eine Antwort.",
        5: "Toi rat lo lang vi chuyen nay anh huong den diem tin dung cua toi. Xin hay giup toi giai quyet van de nay som.",
        6: "Sono cliente di questa banca da molti anni e non ho mai avuto problemi del genere. Aspetto una risposta da settimane.",
        7: "Matagal na akong customer ng kumpanyang ito at hindi ko maintindihan kung bakit ito nangyayari. Kailangan ko ng tulong agad.",
        8: "Jestem klientem tego banku od wielu lat i nigdy wczesniej nie mialem takiego problemu. Prosze o szybka odpowiedz i wyjasnienie tej decyzji.",
        9: "Bu durum beni cok uzuyor cunku ev almak icin kredi kullanmam gerekiyor. Lutfen bana yardim edin, ne yapacagimi bilmiyorum. Simdiden tesekkur ederim.",
        10: "qwerty asdfgh zxcvbn poiuyt lkjhgf mnbvcx qazwsx edcrfv tgbyhn ujmik olp",
        15: "Llevo muchos anos como cliente de este banco y nunca habia tenido un problema asi. Espero una respuesta pronto.",
        16: "Main bahut pareshan hoon kyunki mujhe naya loan lena hai aur ab credit score ki wajah se mushkil ho rahi hai.",
        17: "J'ai envoye une lettre recommandee il y a un mois et je n'ai toujours pas recu de reponse de leur part.",
        19: "Zhe jian shi rang wo feichang danxin, yinwei wo de jiating xuyao zhe xie qian. Qing jinkuai huifu wo.",
    }
}

CATEGORIES = {
    "investment_advice": INVESTMENT,
    "legal_advice": LEGAL,
    "decide_outcome": DECIDE,
    "non_finance": NON_FINANCE,
    "non_english_or_unreadable": NON_ENGLISH,
}
# per category: (val, test); the rest is train. Totals: 90 / 10 / 20.
SPLIT = {
    "investment_advice": (2, 5),
    "legal_advice": (2, 4),
    "decide_outcome": (2, 5),
    "non_finance": (2, 3),
    "non_english_or_unreadable": (2, 3),
}

MIN_WORDS = 50
SEED = 42


def extend(category, i, text):
    """Append context sentences until the text has at least MIN_WORDS words."""
    if len(text.split()) >= MIN_WORDS:
        return text
    if i in EXTRA_BY_INDEX.get(category, {}):
        text += " " + EXTRA_BY_INDEX[category][i]
    pool = EXTRA.get(category, [])
    j = 0
    while len(text.split()) < MIN_WORDS and j < len(pool):
        text += " " + pool[(i + j) % len(pool)]
        j += 1
    assert len(text.split()) >= MIN_WORDS, (category, i)
    return text


def examples():
    """All 120 examples as dicts with id, category, split and text (fixed split, seed 42)."""
    import random
    rows = []
    for category, texts in CATEGORIES.items():
        order = list(range(len(texts)))
        random.Random(f"{SEED}-{category}").shuffle(order)
        n_val, n_test = SPLIT[category]
        split = {i: "val" for i in order[:n_val]}
        split.update({i: "test" for i in order[n_val:n_val + n_test]})
        for i, text in enumerate(texts):
            rows.append({"complaint_id": f"oos-{category}-{i:02d}", "category": category,
                         "split": split.get(i, "train"), "narrative": extend(category, i, text)})
    return rows
