odoo.define('iziWidget.IconWidget', function (require) {
    "use strict";
    var registry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');

    var SentimentIconWidget = AbstractField.extend({
        className: "izi_sentiment_icon",
        events: {
            'mouseover > a': '_onMouseHover',
            'mouseout > a': '_onMouseLeave',
            'click > a': '_onClick'
        },
        supportedFieldTypes: ['selection'],
        // indexIcon: ['fa-frown-o', 'fa-meh-o', 'fa-smile-o'],
        indexIcon: [
            // '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M15.877 6.124l-3.877 3.876-3.877-3.876 1.124-1.124 2.753 2.753 2.754-2.753 1.123 1.124zm-3.877-4.124c5.514 0 10 4.486 10 10s-4.486 10-10 10-10-4.486-10-10 4.486-10 10-10zm0-2c-6.627 0-12 5.373-12 12s5.373 12 12 12 12-5.373 12-12-5.373-12-12-12zm.001 14c-2.332 0-4.145 1.636-5.093 2.797l.471.58c1.286-.819 2.732-1.308 4.622-1.308s3.336.489 4.622 1.308l.471-.58c-.948-1.161-2.761-2.797-5.093-2.797zm-3.501-5c-.828 0-1.5.671-1.5 1.5s.672 1.5 1.5 1.5 1.5-.671 1.5-1.5-.672-1.5-1.5-1.5zm7 0c-.828 0-1.5.671-1.5 1.5s.672 1.5 1.5 1.5 1.5-.671 1.5-1.5-.672-1.5-1.5-1.5z"/></svg>',

            '<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" viewBox="0 0 56 56" enable-background="new 0 0 56 56" xml:space="preserve">  <image id="image0" width="56" height="56" x="0" y="0"\n' +
            '    xlink:href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADgAAAA4CAMAAACfWMssAAAABGdBTUEAALGPC/xhBQAAACBjSFJN\n' +
            'AAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAACKFBMVEUAAADuZjHuZjHuZjHu\n' +
            'ZjHuZjHuZjHuZjHuZjHuZjHuZjHuZjHuZjHuZjHuZjHuZjHuZjHuZjHuZjHuZjHuZjHuZjHuZjHu\n' +
            'ZjHuZjHuZjHuZjHvaDPybzr0dD/2eEP4e0b4fUjxbTj3ekX8g07/i1b1dkH8hVDuZzL2d0L+iFP9\n' +
            'hlH3e0bvaTT7gk3wajXvZzL8hE/5fkn0cz7/ilX3eUT9iFPqg1TLdlLYe1PeflPlgVTmgVTyhlX6\n' +
            'iVbfflToglT7g052VEsvOEYxOUY7PUdDQEi2blC1bVAwOEZ7Vkz+iVT9ilbEc1JKRElbYm5RWWVd\n' +
            'S0peZHBJQ0jCc1HkgFTwaTTAclFIUF13fIddY28wOUaIXE1yU0tTRklCP0ezbVBzU0s7RFBscn3x\n' +
            'bDd9V0xFTVptcn46QlCoaE9vdIBES1nybjlcSkmFW01XSEmAWEzwazZsUEuWYU6hZk/9h1LvhFVV\n' +
            'R0n+i1b6gUy7cFHbfVPReFJYSEl+WEz1h1W6b1GDWkw5PEc0OkZOREh8V0zPeFLVelM2O0d1VEv3\n' +
            'iFXMdlJeS0o1Okc8PUc1O0bgf1RrUEtHQUjngVTzcTz7iVaYYk41OkY6PEfNd1L8ilb4fEfif1Ra\n' +
            'SUlUR0mtalD2h1X4iFUyOUZKQ0i/cVE6PUdnTkrIdVJ3VUvUelOkZ09wUktjTUrhf1S5b1HdfVPs\n' +
            'hFSLXU3ZfFP6f0r1dUD+ilX5f0r6gEv///9n9BXhAAAAGnRSTlMACEB8o8zo9Apat/cZkPMPk/pb\n' +
            '6QykI9cw8Up8Z9oAAAABYktHRLfdADtnAAAAB3RJTUUH4gcbAjcwFzpYUQAAA9tJREFUSMeVl/lf\n' +
            'E0cYhxdIFhMMV4DAuxEMjIREElCgAcQWN8Ej2EpbtLaWlhZaaDlEiYKCrSj28GhV7CFWqz3p3Yr6\n' +
            '9/Wdycwm2WySzfcHPvMeDzvM9b5IkoEKCossVrkYoFi2WooKCyRT2mKzl4Di3lbfsH17Q/02twIl\n' +
            'dtuWnNhWRyl4GptIkpoaPVDq2JoVKyuvUHY0kzQ171Aqyssyc5VOb4uPGMrX4nVWZsCqqsHtJxnl\n' +
            'd0N1lRFX4/LuJFm10+uqSedq5dYAyaFAq1ybxtUF/bk4nG6wTkfWyGY4Ssops61ytbWb4Qhpb3Ml\n' +
            'r1A17DLHEbILqpP2D3ab5QjZDdp+ljlbfeZBX6tTnKFyaDDPEdIA5fxcVwQ78gE7ghXxE++Aznw4\n' +
            'QjrBwe5fqbcrP7DLW0rvpw3c+XGEuMGGoB0amfVcqLu7p3dPX9/e9My9fX17ep/v7g69wMxGsOP7\n' +
            'UgL9zNqnagpHBvYL5sBA5GAicoj5+qGkQCoEiDJrsPfwiy8dERlDAhxi5pGX8ccrrw4PMl8UoFAq\n' +
            'gqMi59hrx1/H+Bsn3hx564Bwvj0wMnrinePvUvyYcB6FIskCY8Icf+/9CRqf1P+JkxMffEgD48Ix\n' +
            'BhbJClPCnObTnNGDMzwwLRxTYJVk8AhzlsdP6sGTPDArHB6QpWKYE+YpHj+tB0/zwCnhmINiCUAR\n' +
            '5jyPh/RgiAfmhUMBQBBi3DwTYeGzC3pw4SwLRM5wO4YQThUWRcK5MA2fTz855+mvDJ8T5iKWI1wc\n' +
            'aNESlkaXLwwTAw1fWB5d0qwWwMWxQmJZzcoDuB0WnG9zflwzIhY8cslzTdVHH1+cXVEvXV69kuLG\n' +
            'meKRw0MOStQI+2T1U+1WfPZ5wh/FzcBDjtcKoD4du3otjly/8QUjE5F6BPBa4UXGT8Z02Jc3afat\n' +
            'i/tvoxEawXGvCMXoB+3s6UCtpWB3vvpaVb+Z+XaQ23dXVLVHBNdovo09VnS0nsTd+05V7z/4PuF4\n' +
            '+Ej94S4fr9Ns9ljh84jy9mtpP/6k/vxLygx+VSMbfNjvpdkO/iDTsVbmfgv/vpGCkcnwH3/yoT9I\n' +
            'c/mDjCWAkXyB/vpbt1D//PuftjCMEyUAi06czFki2+OcVnSwzDEpj7Nzj5V4XmVyYY1r80lm7Mkm\n' +
            'T0oqrFjKuTP4NBP3NMhTUko5Ng/cDVPPjLBnUyIu61qd2joRgbFOXQPi7xzTgnXpjY72TdTc5nog\n' +
            'hlcmGgusb84lBdIbJNqSQU4ZtWSsCcwh4yaQ7qczG5ax7ZRYo5sJy9roSvHW2kC5WmvWTNBmPkWm\n' +
            'mnkmM/8+/A9yZJ3HoHE4VwAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAxOC0wNy0yN1QwMjo1NTo0OC0w\n' +
            'NzowMKvI00IAAAAldEVYdGRhdGU6bW9kaWZ5ADIwMTgtMDctMjdUMDI6NTU6NDgtMDc6MDDalWv+\n' +
            'AAAAAElFTkSuQmCC" />\n' +
            '</svg>',
            '<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" viewBox="0 0 56 56" enable-background="new 0 0 56 56" xml:space="preserve">  <image id="image0" width="56" height="56" x="0" y="0"\n' +
            '    xlink:href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADgAAAA4CAMAAACfWMssAAAABGdBTUEAALGPC/xhBQAAACBjSFJN\n' +
            'AAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAACH1BMVEUAAAD1wzr1wzr1wzr1\n' +
            'wzr1wzr1wzr1wzr1wzr1wzr1wzr1wzr1wzr1wzr1wzr1wzr1wzr1wzr1wzr1wzr1wzr1wzr1wzr1\n' +
            'wzr1wzr1wzr1wzr1wzr1wzr1wzr1xD32yEf3yk74zVX4zln5z1z2x0X4zlf602b713D713H1xDz4\n' +
            'y1H61Gj1wzv4zFP71m33yEj61Gn1xD760mP2xUD50F72xT/YvGq9p2Thw2zvzm5pZlIvOEYwOUaH\n' +
            'fVn51nFrZ1NUW2dMU2CVh1tKUl5WXWn61WzGrmZGTlt3fIdeZXEzO0fpyW08Q092e4Zuc3+BeFdJ\n' +
            'UV1yd4M+RlOqmGA8RFF1eoVJUV74zlhdXFCFe1j60mRVVU59dVf71m5pZVKRhFuZilzBqmX2xkPl\n' +
            'xmw2PkhMTkz51XD2x0apl2A1PUfLsme7pWRcW09CR0rSt2j2xkL61Wv50mL4zFT2x0TixGzJsGfe\n' +
            'wWtTVE7uzW7oyG1valNJTEuJfllBRkqsmWD41XD103ChkV47QUl7c1ZtaFOmlV/x0G/tzG6djV1G\n' +
            'Skv00W/10nBoZFI5P0hybFSxnWH61nFsZ1M1PEdeXVD3yUqIfVlzbVR1b1VbWk/5z1vDq2VJTUxE\n' +
            'SEq5pGOkk19IS0tDSErz0W9KTUxHS0t9dFa/qGT2xUHNs2e1oWK1oGLMsmfqym3602f50WD3y1H7\n' +
            '1m/50F/4zVb61Gr3y1D///+j8jK3AAAAHXRSTlMACEB8o8zo9Apat/f2GZDzD5P6klvpDKQj1zDx\n' +
            '+ci933UAAAABYktHRLRECWrdAAAAB3RJTUUH4gcWFAYXnqztlwAAA8FJREFUSMeVl2dDE0EQhg+S\n' +
            'HCRCAgmhOgEihAuEGvopKAoWVFRUlN5RKaHYCyCoYMGKBewNKwL6B9297B7J3aXNF27mnYdbbmd3\n' +
            'BoZRsLBwlVrDRgBEsBq1KjyMCcoitbotYElNS7du22ZNT0u1QJROGxkQi9YbICPTlsWJlmXLzACD\n' +
            'PtovFhNrtGfncDLLybYbTTG+uTizIzePU7S8XIc5zgcWnwD5BZxPK8iHhHglLjHJYeX8mtWRlCjn\n' +
            'ktnCIi6AFRWyyTIuxVkQiEPLdaZIyEQ2GA6TrNdq45PstmA4jrPZkzy/UAIUB8dxXDEkeOwfpAXL\n' +
            'cVwaiPsZYy7JCx7MKzHTGooFcQNLy8qV08vLSumjFUykro1OUtMVlTy/fUeVHKvasZ3nKyvcTpbT\n' +
            '6K54PWQSvXrnLp7na+Rgze49SKgmXibohfNncNS6A3V79+1H+oF6KVd/8NBhJPB1brfWYcDnUwv5\n' +
            'RG84cvQY1hulYOPxEyex0ED8fNAiUAdNxD/Fu+20FDxNhFPEbwIdul+2QDPxW4jeKgVbidBC/GaI\n' +
            'CmPCAdqI3070DinYQYR24rcBhDMqKKF6J9G7pGAXETppoARUjBq6qdvTK8h9/VKwv08QentooBvU\n' +
            'jAYGxIQzWD57Tr6P585i5YzoD4CGYSFjM2FwaLh9hFOwkcrhocFNNwNYJgJcXMjmgggGwBI6aAFA\n' +
            'IIyGyo0iCC0VxkIFx1A7Qh8HxkMFxwF9HA3ARKjgBKDtUKP1im3m/Ijv7AsX6VMOQtSo5AByaegS\n' +
            '33pZGbtylb9Gn3MRosJFDhZa5td5/sbklBybvjnD87PEaUObgYo8LAr9SCexqVu4Vm/f8cbm5u+i\n' +
            '8NA94qYjAB0rdJDRK+lW3n+Ai3Lh4aNyEnh8cfLJUxx7Rq4qbhS/UCdcHcgW6W+fek6O0MyzF7Mv\n' +
            '218t0MM9TTMWcb5WuKzw05K4sOXXvMzevBXlJZwtXFboekTm0XSm3733xj7MfxRFmx1n68mFjJ89\n' +
            '21zVcsMnSn3+8tXjMxc4ce5WMoKYsAMr3rU+9+375OSPn7+8gqMrQqpJbDqC6/wdqNR+C+8Dsemg\n' +
            'NieYZdU/t2px58V5Nla3/Vnzja39IUkejRW1chJ0rvvi1p0kxauVo+GBhGFAcb2rA1RnJaNOcgpV\n' +
            'wLXx15v6u+ESxRT5oCO+E7P/lppr0d+7Vtu89M/lIcgHJDySQUBTGsmEITCAKQ+BeD/N/jCfYyeu\n' +
            'IZPRF7bV36DLuEdrBQs0WgvDhFYX5U0FNcwLFsy/D/8B8ga5rYZzTrIAAAAldEVYdGRhdGU6Y3Jl\n' +
            'YXRlADIwMTgtMDctMjJUMjA6MDY6MjMtMDc6MDAOqzWOAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDE4\n' +
            'LTA3LTIyVDIwOjA2OjIzLTA3OjAwf/aNMgAAAABJRU5ErkJggg==" />\n' +
            '</svg>',
            '<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" viewBox="0 0 56 56" enable-background="new 0 0 56 56" xml:space="preserve">  <image id="image0" width="56" height="56" x="0" y="0"\n' +
            '    xlink:href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADgAAAA4CAYAAACohjseAAAABGdBTUEAALGPC/xhBQAAACBjSFJN\n' +
            'AAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAABmJLR0QA/wD/AP+gvaeTAAAM\n' +
            '+UlEQVRo3s2bW2xc13WGv73Pdc6ZG++SLEtVZMiSkLZ2ZCkOG1YXFIgNWXCcIEELy9GDC1QoFAco\n' +
            'CtQvAQy0L31oH5Sg6EOd1rWFFgnQJnUEpEAfqjIljLjNrYUviR1VikxSJMUZDuecmTm33YczMxxq\n' +
            'LhxKspXFlzMz+6y1/r32XnuttRcF95i82WkbeBz4NPAwcAjYDWQBtzUMqAI3gLeBd4HvA2+4M3P1\n' +
            'e6mPuEegHOCzwHPACcBGaAjdQUgLoVkgdITQAFAqBhWh4gYqaaAiH1QMUAOuAK8C33Zn5vz7CtCb\n' +
            'nd4J/AnwPJAVuou0RpFGAaE722CvUJFPEq6RNFZRkQephV8G/tydmVv4SAF6s9MF4M+AP0BIQ7Mm\n' +
            'kJkphJa5m/nagBvXSGo3iRvLoJIQ+Gvgq+7M3NqHDtCbnX4W+EsQk1pmByLZifdfMY1fhMSVBGkK\n' +
            'jAd0nE+YmHv0oXgG1yP8HwaEH0QkgULLS6yPGbiPaSi5QFxbBNQS8EfuzNylDwWgNzudbc7ks9LI\n' +
            'o2X34b8pKL/uoxqq5zuZ3zQZ+YKLtHuLSeqK0rc8aj8JeitnCYpnHJyjirh6lSSsAFwCzrszc9W7\n' +
            'Anj19Dkd+BiQyZ++qdu/XnkNxEHN3YOW2cH6lTprr6c+QLcsLNdB03WSOKbh+YT11BmaD+pM/GEO\n' +
            'YWwWpULF8l+tE/wyAsCwbSzXQWoacRTR8HyiRgOAwhmH3HGbuLZI7F0H1Dv1/8mfrVyeikgd0y/2\n' +
            'XX4lGgrg1dPndgNfBb4AjLS+1ycDcsczuMcKBDcili5WQIE7UiRTKHQxrlUqeKslALIzNsWnnU2/\n' +
            'l7/jU51NJ8EdHSGTz3fzWFvDK5VBwOQLeczdOt4P1li/UiNaMjuHloBvAX+67/IrN/oCvHr63Gng\n' +
            'm4ADoBkGmpHuozgMicMI+6CBChWN9yMs1yU3Md53eVSWlgj8GkjY9dII0knFJb5i/qUSJGA6GfKT\n' +
            'k315rC+v0PA8rP06whDU3wnRDB3NMJp6RcRh2BruA1/cd/mVy10Ar54+9zjwH4BhZDJkR0faTFoU\n' +
            'hyF+uUzD8xFCMPLALqTe35E0PI/15RUARn/PxTlipVr8d4PVf/AAyE2MY7luXx5JFFH6YB6lFJbr\n' +
            '4BSLPfWqrpYIazWAEPjtfZdfeQNANsFJ4BuAYTkOhanJLiYti+YmJsgU8ljZ7EBwAFLT2s/hzbjn\n' +
            'c+eYnjx0HSubJVPIk5uY6KtXYWoSy3EADOAbTUwpQOAUcEgIQXZ8jK3IHRnBKRa3HJfEG0CQqufz\n' +
            'pjF9yCkWcUdGthyXHR9DCAFpeHiqE+AJAN22EVJuySid+a3HhbWNsFIfVT2fO8fcjSwAISW6bbc+\n' +
            'nuwEOAUgxT0JTQGax0W6z4QO9sENJe2DEtFc3Q3PG8qKw1IHhslOgGsA8T0U5JfXUCq1lHM0Qrob\n' +
            'AKUrcY6mx5ZSCr+87QisL3VgWOsE+COAKAjuyWzGUUS9mgYaMqPInghBdDgToZE9ESIz6QTUq1Xi\n' +
            'KLoTUZsoiWOioB0V/bgT4OtCVwFK4ZfKdy3IL5Whab3syRDpaAi54f2ENJCORvZk8/xSCr9Uumdy\n' +
            'ha4C4F/aACdf/HmUPbnSns3qyq328touRUHQ3nv6RIJ7LEIaua5x0sjhHovQJxKANDQLgm3JapFS\n' +
            'iurKrfaqyZ5cYfLFn0dtgMBnM0fKpvPYehtkeX6BsN7YtjCvwxL5J0PQ9GZuuJmE7oCmp2N6vDss\n' +
            'hfUG5fmFNjjnsXUyR8omaQLeBvgcQP6phOLnA4SZRgdri4tUb62ikuGsGdRqbbdvHYixHoqRRp7e\n' +
            'Mb1AGnmsh2KsA+m+D2t1gjQa2dpqiaJ6a5W1xUXiMESYUPx8QP6ppDXkOQDRrKGUANsoHCKJ60RL\n' +
            'EaV/NImWUvxS18mOjmA6zkCh5fmFdJlpMHGhhj6ho9lTA9+J6zeJliOWv56BGHTTpLhr5+CJ9H2q\n' +
            'qyWSpmPSJxNGfjdAn9SRmk249jakWcaoJC0Q2QBCd9GscfRJg/HzddxPRSDSeLCytExlaZkk6u1l\n' +
            '69Vqew+5n4zQx1TTeoNJGnn0MYX7yVTZKAjay+12SqK4Q49UN/dTEePn6+iTBpo1jtDbcW0GeFwn\n' +
            'rX6lXq7pyjV7nESWyT/pYR+MKf+TSbwmCHyfUr2OUyxsSm9UkrS9r3QVuRMhSHOoEobQMiBNcidC\n' +
            'aj/RSDyBXypjOc6mqKpWqaRna5IuQa2gKH4uwNwXI3QXaRZpbQUhjWalg09L0tIe7dAi/YA0R5Dm\n' +
            'COa+hIkLdTKPRG0w3mopXY6N1GJ+ea19fuZOhQhbIY0Cw5I0CghbkTuVOpwkjtuHf9QIKM8v4K2W\n' +
            '2uAyj0RMXKhj7kvaem7a5xtYHtZJA9PNB3F7nIuUBom4RfFzAZmPx6y9nlozCgLKCwsYtt3O3o0d\n' +
            'Cc6RaKNUOCQJzUJIC+dIA/9NnXBRUqtUiIKgzbtltcKZIHVKQkNaYwhp9mLYejokSYuyQG9PKaSJ\n' +
            'Zk8hpI11IGbiQh3nyEbU0alA/skQJAhzeOu15ZgFkGw6Njp5O0dSq1kHYoS0mzqZfbi1seyWpBXn\n' +
            'VuG1j3SJtMcQRh5hKQpPB4yea6AVNybFPhyn+0HLDBA8SES6Z819MfbhDV20omL0XIPC0wHCUggj\n' +
            'j7THQAzIMDawZCXNcnpzUw5SAWnkkdY4CA1rf8zEhRrOsQhhQv4z6X4UQ3jOvhKaEU/+M+lZ7ByL\n' +
            'mLhQw9rfWpLjA87VDnwbWFzhzU63zWCMPjrU7CsVkzRWIdkc6QjNQVqjdwwQSCvb8W0Ve2khrdF2\n' +
            '6X8wuIBw9Ucbr5JehKQ/xsNFEUJoaPY4Qu+MMcVdWa/N5TYLCT2XyhoCXA8Mnk56B5Au06ACW7j3\n' +
            'ai3m+mJANqMxOZrDsmxU5CE0GyGHq2QPBCh1pDmCiusI3aURGywthlRrMXt2mGQzg4GqoLJJXZ30\n' +
            'CmsKIAnLaDzY9+UfvOXxxxev4zfa8R4jOZ0Hp0x2jftMjq4zXtAZL+qMFwxyjsTNaOSc1CG0ku1W\n' +
            'orLuJ3i1mHU/YWUtZKUcsbIWsbQaMr8S8suby5TWNzy2Y0n+4it7OHpoQBUuLHd+vKGT3s8dAVCR\n' +
            'j4prfSOQv7u8vAkcQGk9orQe8dP37tp4W5LfSPjb7y73BajiWnoVt0FvS9LLx40ZqC/3FbDuJ9xv\n' +
            'qg7QoYfu70rSm9U2xfWlvmfi3h3bP9/uNe3d2UcHFae6b6bvS+AN0tRiY2Ct933j8Udz3G86/mhv\n' +
            'Tx3XFm43TA14QzbvxK9sHryISrrLB6cey7Nn6v5Zcc8Ok5NHuidZJUHzDnETXXFn5uqteOfVzW/E\n' +
            'xNWrXYw0KXjxS7vuG8AXn9uFJrujmLh6tde2ehU2ShbfJj0P25QEZZLuNc2xwy7nn+l/G/Rh0fln\n' +
            'Jjl2uNt7JvUlkqB8+9fVJiZ0AHdmzvdmp18GvtI5KvKuYehuZ5YMwPNnJlj3Yy79662+Co1pGp8w\n' +
            'MxwwLHbpBuNSw2oGyA2VsJLEzEchPwsb/DCocWtAPfbsE2M8f2ai63sVeUTetV6vvNzq0Gjbu9kx\n' +
            'cY30dqZNQprohUMIze7i8tr3bnHxm4u0alIagt/JZHnGzfNx02Y79L9BnX/2KvxbrUrcTHekgBe+\n' +
            'uIOzT3RfCKm4TrT2di9fEQC/1urM2LSgvdnpi8CXb39DSAu9eLhnIP7T93xe+psP2FvW+XJuhDFN\n' +
            'R5ca2jbvORKliFTCShTy9fUS/1eMeOn3H+A3HuoudKkkICq/hUp6ljW/5s7MvdDW/TaABeBnNC8u\n' +
            'uiyZf7hnjTOMFG9dXGNsQbXjMAFoQiKFQApB+tcBCIVSihhFnChUK0kVgls7BYdfKGDo3ZOkIp+o\n' +
            '8m5PLw8sAQc62026ODTbRF7rOc1CQ8/tb9ZAuqlRTXjv79fJXEsw4+1VxgNNUNsreehLOaxs72Q2\n' +
            'CUpE6+8PSs7P3t5m0nMdebPTrwHP9uMi7Sl0d8/ArLp8I2L+333UtQSrqjBiEE3MSkCoQSMrEHsl\n' +
            'u044FHcPyERUQuRdJ6nfHDRHl9yZubNdNukDMAu8CRzsx01IE83de9cJ7laUNFaJvWv9lmSL3gGO\n' +
            '9uqd6esJvNnp/cB/0kyl+gLVs2jOrr7L9o6BBSVifx4VbdnvcxP4LXdm7v2e+g1605udfoQ0jNsy\n' +
            'VReandZMrPFtlQw7ScUNksYKSWMFFQ/VVVkBjrszcz/uq9dWHJogv8cWlrwdrDDySN1Nc0vNTksO\n' +
            'rT2rkrSlMq6njXeRhworw4Jq0U3giUHghgLYBLkf+C4D9uRHTO8AT/Vblp00VPtCk9FR0ka4+02X\n' +
            'SB3KluDgrtop+agj7jtqpxyuAaWDmgIOAF8jbZv6sCloyjqwXXBwj1ua7zGw+9fS3ANoZ1P6cdLL\n' +
            'xzuhX62m9D5gf6X+reD/AXT2dKP6SqTQAAAAJXRFWHRkYXRlOmNyZWF0ZQAyMDE4LTA3LTI2VDE5\n' +
            'OjUyOjM3LTA3OjAwYTd+jwAAACV0RVh0ZGF0ZTptb2RpZnkAMjAxOC0wNy0yNlQxOTo1MjozNy0w\n' +
            'NzowMBBqxjMAAAAASUVORK5CYII=" />\n' +
            '</svg>',
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 0c-6.627 0-12 5.373-12 12s5.373 12 12 12 12-5.373 12-12-5.373-12-12-12zm3.5 8c.828 0 1.5.671 1.5 1.5s-.672 1.5-1.5 1.5-1.5-.671-1.5-1.5.672-1.5 1.5-1.5zm-7 0c.828 0 1.5.671 1.5 1.5s-.672 1.5-1.5 1.5-1.5-.671-1.5-1.5.672-1.5 1.5-1.5zm8.122 9.377c-1.286-.819-2.732-1.308-4.622-1.308s-3.336.489-4.622 1.308l-.471-.58c.948-1.161 2.761-2.797 5.093-2.797s4.145 1.636 5.093 2.797l-.471.58z"/></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M22 12c0 5.514-4.486 10-10 10s-10-4.486-10-10 4.486-10 10-10 10 4.486 10 10zm2 0c0-6.627-5.373-12-12-12s-12 5.373-12 12 5.373 12 12 12 12-5.373 12-12zm-14 6v-12c-1.465.331-4 2.827-4 6.001 0 3.134 2.521 5.665 4 5.999zm3.998 0l-.506-.755s.947-.503.947-1.746c0-1.207-.947-1.745-.947-1.745l.506-.754c.748.281 2.002 1.205 2.002 2.499 0 1.295-1.254 2.218-2.002 2.501zm0-7l-.506-.755s.947-.503.947-1.746c0-1.207-.947-1.745-.947-1.745l.506-.754c.748.281 2.002 1.205 2.002 2.499 0 1.295-1.254 2.218-2.002 2.501z"/></svg>'
        ],
        /*activeClass: [
            'izi-icon-angry',
            'izi-icon-frown',
            'izi-icon-meh',
            'izi-icon-smile',
            'izi-icon-hz-smile'
        ],*/
        isSet: function () {
            return true;
        },

        _renderReadonly: function () {
            if(this.attrs.show_all_icon  && this.attrs.show_all_icon === 'true') {
                this.$el.empty();
                var self = this;
                var index_value = this.value ? _.findIndex(this.field.selection, function (v) {
                    return v[0] === self.value;
                }) : 0;
                this.$el.empty();
                // this.empty_value = this.field.selection[0][0];
                _.each(this.field.selection, function (choice, index) {
                    self.$el.append(self._renderIcon('<div>', index_value === index, index, choice[1]));
                });
            } else {
                this.$el.append(
                    $('<div>')
                        .attr('hint-tooltip', this.field.selection[this.value][1])
                        .attr('data-index', this.value)
                        .addClass('izi_sentiment_icon izi-sentiment-active')
                        .append(this.indexIcon[this.value])
                );
            }
        },
        _renderEdit: function () {
            var self = this;
            var index_value = this.value ? _.findIndex(this.field.selection, function (v) {
                return v[0] === self.value;
            }) : 0;
            this.$el.empty();
            _.each(this.field.selection, function (choice, index) {
                self.$el.append(self._renderIcon('<a href="#">', index_value === index, index, choice[1]));
            });
        },

        _renderIcon: function (tag, isActive, index, tip) {
            return $(tag)
                .attr('hint-tooltip', tip)
                .attr('data-index', index)
                .toggleClass('izi-sentiment-active', isActive)
                .toggleClass('izi-sentiment-icon-default', !isActive)
                .addClass('hint hint--top hint-persist izi_sentiment_icon').append(this.indexIcon[index]);
        },

        _onClick: function (event) {
            event.preventDefault();
            event.stopPropagation();
            if (this.mode === 'edit') {
                var index = $(event.currentTarget).data('index');
                var newValue = this.field.selection[index][0];
                if (newValue === this.value) {
                    return;
                }
                this._setValue(newValue);
            }
        },

        _onMouseLeave: function () {
            if (this.mode === 'edit') {
                clearTimeout(this.hoverTimer);
                var self = this;
                this.hoverTimer = setTimeout(function () {
                    self._render();
                }, 200);
            }
        },

        _onMouseHover: function (event) {
            clearTimeout(this.hoverTimer);
            console.log('event');
            this.$('.izi_sentiment_icon').removeClass().addClass('izi_sentiment_icon hint hint--top izi-sentiment-icon-default');
            var target = $(event.currentTarget);
            var index = target.data('index');
            // target.parent().find('#selection-title').remove();
            target.removeClass('izi-sentiment-icon-default').addClass('hint hint--top hint-persist izi-sentiment-active');
            // target.append('<p id="selection-title">'+this.field.selection[index][1]+'</p>');
        }
    });
    registry.add('sentiment_icon', SentimentIconWidget);
});
