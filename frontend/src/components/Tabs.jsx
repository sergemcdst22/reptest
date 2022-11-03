import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Button, Form } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import './Tabs.css';
import axios from 'axios';


function FormTodo({ addTodo }) {
    const [value, setValue] = React.useState("");

    const handleSubmit = e => {
        e.preventDefault();
        if (!value) return;
        addTodo(value);
        setValue("");
    };

    return (
        <Form onSubmit={handleSubmit}>
            <Form.Group>
                <Form.Label><b>Добавить артикул</b></Form.Label>
                <Form.Control type="number" className="input" value={value} onChange={e => setValue(e.target.value)} placeholder="введите артикул" />
            </Form.Group>
            <Button variant="primary mb-3" type="submit">
                Добавить
            </Button>
        </Form>
    );
}

const Tabs = () => {

    const [currentTab, setCurrentTab] = useState('1');
    const interval = useRef(setTimeout(() => { }, 0));



    const [tabs, setTabs] = useState([]);


    useEffect(() => {
        async function fetchCurTabs() {
            let curTabs = await axios.get("https://api.rep-test.ru/articules");
            //console.log(curTabs.data);
            curTabs = curTabs.data;
            let newTabs = [];
            for (let curTab of curTabs) {
                let nameAndPrices = await axios.get(`https://api.rep-test.ru/articules/${curTab}`);
                nameAndPrices = nameAndPrices.data;
                let [name, ...prices] = nameAndPrices;
                name = name.trim();
                prices = prices.map(p => p.trim());
                newTabs.push({
                    id: curTab,
                    tabTitle: curTab + " (" + name + ")",
                    title: name,
                    content: prices
                })
            }
            setTabs(newTabs);
            setTimeout(() => {
                if (newTabs.length > 0) {
                    document.getElementsByClassName("tabs")[0].children[0].click();
                }
            }, 100);
        }
        fetchCurTabs();
    }, []);


    const addTab = async (text) => { 
        await axios.get(`https://api.rep-test.ru/addarticule/${text}`);
        let newTabs = [...tabs];
        let nameAndPrices = await axios.get(`https://api.rep-test.ru/articules/${text}`);
        nameAndPrices = nameAndPrices.data;
        let [name, ...prices] = nameAndPrices;
        name = name.trim();
        prices = prices.map(p => p.trim());
        newTabs.push({
            id: text,
            tabTitle: text + "(" + name + ")",
            title: name,
            content: prices
        });
        setTabs(newTabs);
        setTimeout(() => {
            const n = newTabs.length - 1;
            document.getElementsByClassName("tabs")[0].children[n].click();
        }, 300);
    };


    const removeCur = async () => {
        await axios.delete(`https://api.rep-test.ru/articules/${currentTab}`);
        const newTabs = tabs.filter(function (item) {
            return item.id != currentTab;
        })
        setTabs(newTabs);

        setTimeout(() => {
            if (tabs.length > 0) {
                document.getElementsByClassName("tabs")[0].children[0].click();
            }
        }, 100);
    };


    const addInfo = async () => {
        console.log("add info: " + interval.current + "; tabs count: " + tabs.length);
        let newTabs = [...tabs];
        for (let i = 0; i < tabs.length; i++) {
            const tab = newTabs[i];
            const prieDateNameInfo = await axios.get(`https://api.rep-test.ru/read_price/${tab.id}`);
            //console.log(prieDateNameInfo);
            let [price, date, name] = prieDateNameInfo.data;
            //console.log(`price=${price} date=${date} name=${name}`);
            if (tab.title == "?" && name != "?")
                tab.title = name;
            if (tab.content.length > 0 && tab.content[0].split(" --- ")[0] != price) {
                tab.content = [`${price} --- ${date}`].concat(newTabs[i].content);
                tab.content = tab.content.slice(0, 10);
            }
        }
        setTabs(newTabs);
    };

    useEffect(() => {
        interval.current = setTimeout(addInfo, 60000);
        console.log("use effect set timeout : " + interval.current + "; tabs count: " + tabs.length);
        return () => {
            console.log("use effect clear) : " + interval.current + "; tabs count: " + tabs.length);
            clearTimeout(interval.current); // cleanup
        };
    }, [tabs]);


    const handleTabClick = (e) => {
        setCurrentTab(e.target.id);
    }

    return (
        <div className='container'>
            <FormTodo addTodo={addTab} />
            <hr></hr>
            <h1 className='tyty'><b>Информация по ценам</b></h1>
            <div className='tabs'>
                {tabs.map((tab, i) =>
                    <button key={i} id={tab.id} disabled={currentTab === `${tab.id}`} onClick={(handleTabClick)}>{tab.tabTitle}</button>
                )}
                <Button variant="outline-danger" onClick={() => removeCur()}>✕</Button>
            </div>

            <div className='content'>
                {tabs.map((tab, i) =>
                    <div key={i} className="nar">
                        {currentTab === `${tab.id}` && <div><p className='title'>{tab.title}</p><ul className='contentsc'>{tab.content.map((c, ii) => <li key={ii}>{c}</li>)}</ul></div>}
                    </div>
                )}

            </div>
        </div>
    );
}

export default Tabs;
