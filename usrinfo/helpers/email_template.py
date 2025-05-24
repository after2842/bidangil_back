def render_order_email(user_nickname, order_id, detailed_message, payment_url):
    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
      <meta charset="UTF-8">
      <title>주문 접수 확인</title>
      <style>
        body {{
          margin: 0;
          padding: 24px;
          background-color: #ffffff;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          color: #000000;
          line-height: 1.6;
        }}

        .header {{
          color: #3B82F6;  /* Tailwind blue-500 */
          font-size: 20px;
          font-weight: 700;
          margin-bottom: 20px;
        }}

        .section {{
          margin-bottom: 18px;
        }}

        .highlight {{
          font-weight: bold;
        }}

        a.button {{
          display: inline-block;
          padding: 10px 18px;
          color: white;
          background-color: #3B82F6;
          text-decoration: none;
          border-radius: 6px;
          margin-top: 12px;
        }}

        .footer {{
          font-size: 14px;
          color: #555;
          margin-top: 32px;
        }}
      </style>
    </head>
    <body>

      <div class="section">안녕하세요, <span class="highlight">{user_nickname}</span>님 😊</div>

      <div class="section">
        고객님의 주문이 접수되었습니다.<br>
        결제 완료 후 <strong>비단길에서</strong> 상품의 구매를 시작합니다.
      </div>

      <div class="section">{detailed_message}</div>

      <div class="section">
       <a href="{payment_url}" class="button">결제하기</a>
      </div>

      <div class="section">
        <strong><a href="https://bidangil.co"">비단길 웹사이트</a> → 내 정보</strong> 메뉴에서도 결제 및 주문 정보를 확인하실 수 있습니다.
      </div>

      <div class="footer">비단길을 이용해주셔서 대단히 감사합니다</div>
    </body>
    </html>
    """


from html import escape

def order_message(urls, descriptions, prices):
    """Return an HTML fragment for detailed_message."""
    blocks = []

    for idx, (url, opt, price) in enumerate(zip(urls, descriptions, prices), start=1):
        # -- visible text for the link (truncate to 40 chars) --
        visible = (url[:30] + "…") if len(url) > 40 else url

        block = f"""
        <p style="margin:0 0 16px 0; line-height:1.5;">
          <strong>상품{idx}</strong><br>
          <a href="{escape(url)}" target="_blank" rel="noopener noreferrer">{escape(visible)}</a><br>
          <strong>옵션:</strong> {escape(opt)}<br>
          <strong>가격:</strong> {float(price):,.0f}원
        </p>
        """
        blocks.append(block.strip())

    # Two blank lines (= 2×<br>) between items
    return "<br>".join(blocks)



def render_delivery_email(user_nickname, order_id, detailed_message, payment_url):
    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
      <meta charset="UTF-8">
      <title>주문 배송 대기</title>
      <style>
        body {{
          margin: 0;
          padding: 24px;
          background-color: #ffffff;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          color: #000000;
          line-height: 1.6;
        }}

        .header {{
          color: #3B82F6;  /* Tailwind blue-500 */
          font-size: 20px;
          font-weight: 700;
          margin-bottom: 20px;
        }}

        .section {{
          margin-bottom: 18px;
        }}

        .highlight {{
          font-weight: bold;
        }}

        a.button {{
          display: inline-block;
          padding: 10px 18px;
          color: white;
          background-color: #3B82F6;
          text-decoration: none;
          border-radius: 6px;
          margin-top: 12px;
        }}

        .footer {{
          font-size: 14px;
          color: #555;
          margin-top: 32px;
        }}
      </style>
    </head>
    <body>

      <div class="section">안녕하세요, <span class="highlight">{user_nickname}</span>님 😊</div>

      <div class="section">
        고객님의 물건이 배송 대기상태입니다.<br>
        결제 완료 후 <strong>비단길에서</strong> 다음의 주소로 배송을 시작합니다.
      </div>

      <div class="section">{detailed_message}</div>

      <div class="section">
       <a href="{payment_url}" class="button">결제하기</a>
      </div>

      <div class="section">
        <strong><a href="https://bidangil.co"">비단길 웹사이트</a> → 내 정보</strong> 메뉴에서도 결제 및 주문 정보를 확인하실 수 있습니다.
      </div>

      <div class="footer">배송 시작 후, 송장번호와 함께 배송정보를 안내 드립니다.<br>비단길을 이용해주셔서 대단히 감사합니다.</div>
    </body>
    </html>
    """




def purchase_confirm_email(user_nickname):
    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
      <meta charset="UTF-8">
      <title>주문 배송 대기</title>
      <style>
        body {{
          margin: 0;
          padding: 24px;
          background-color: #ffffff;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          color: #000000;
          line-height: 1.6;
        }}

        .header {{
          color: #3B82F6;  /* Tailwind blue-500 */
          font-size: 20px;
          font-weight: 700;
          margin-bottom: 20px;
        }}

        .section {{
          margin-bottom: 18px;
        }}

        .highlight {{
          font-weight: bold;
        }}

        a.button {{
          display: inline-block;
          padding: 10px 18px;
          color: white;
          background-color: #3B82F6;
          text-decoration: none;
          border-radius: 6px;
          margin-top: 12px;
        }}

        .footer {{
          font-size: 14px;
          color: #555;
          margin-top: 32px;
        }}
      </style>
    </head>
    <body>

      <div class="section">안녕하세요, <span class="highlight">{user_nickname}</span>님 😊</div>

      <div class="section">
        고객님이 주문하신 상품들을 비단길에서 구매하였습니다.<br>
        비단길에서 배송준비가 완료되면 최종적인 안내와 배송비 결제 링크를 안내드립니다.<br>
      </div>

      <div class="footer">비단길을 이용해주셔서 대단히 감사합니다</div>
    </body>
    </html>
    """




def render_delivery_info_email(user_nickname, courier, tracking_url, tracking_num):
    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
      <meta charset="UTF-8">
      <title>주문 접수 확인</title>
      <style>
        body {{
          margin: 0;
          padding: 24px;
          background-color: #ffffff;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          color: #000000;
          line-height: 1.6;
        }}

        .header {{
          color: #3B82F6;  /* Tailwind blue-500 */
          font-size: 20px;
          font-weight: 700;
          margin-bottom: 20px;
        }}

        .section {{
          margin-bottom: 18px;
        }}

        .highlight {{
          font-weight: bold;
        }}

        a.button {{
          display: inline-block;
          padding: 10px 18px;
          color: white;
          background-color: #3B82F6;
          text-decoration: none;
          border-radius: 6px;
          margin-top: 12px;
        }}

        .footer {{
          font-size: 14px;
          color: #555;
          margin-top: 32px;
        }}
      </style>
    </head>
    <body>

      <div class="section">안녕하세요, <span class="highlight">{user_nickname}</span>님 😊</div>

      <div class="section">
        고객님의 배송이 시작되었습니다.<br>
        운송사: {courier}<br>
        조회번호:<strong>{tracking_num}</strong><br><br>
        <a href="{tracking_url}" class="button>배송 조회하기</a><br>
      </div>
      <div class="footer">배송조회 링크가 작동하지 않는경우, 운송사 웹사이트에서 조회하실 수 있습니다.</div>
      <div class="footer">비단길을 이용해주셔서 대단히 감사합니다.</div>
    </body>
    </html>
    """



def render_delivery_complete_email(user_nickname):
    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
      <meta charset="UTF-8">
      <title>주문 접수 확인</title>
      <style>
        body {{
          margin: 0;
          padding: 24px;
          background-color: #ffffff;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          color: #000000;
          line-height: 1.6;
        }}

        .header {{
          color: #3B82F6;  /* Tailwind blue-500 */
          font-size: 20px;
          font-weight: 700;
          margin-bottom: 20px;
        }}

        .section {{
          margin-bottom: 18px;
        }}

        .highlight {{
          font-weight: bold;
        }}

        a.button {{
          display: inline-block;
          padding: 10px 18px;
          color: white;
          background-color: #3B82F6;
          text-decoration: none;
          border-radius: 6px;
          margin-top: 12px;
        }}

        .footer {{
          font-size: 14px;
          color: #555;
          margin-top: 32px;
        }}
      </style>
    </head>
    <body>

      <div class="section">안녕하세요, <span class="highlight">{user_nickname}</span>님 😊</div>

      <div class="section">
        고객님의 배송이 완료되었습니다.<br>
        고객님의 소중한 리뷰를 남겨주세요!<br><br>
        <a href="https://bidangil.co/community/review" class="button>리뷰 남기기</a><br>
        우측 상단 프로필 클릭 -> 글 쓰기에서 리뷰를 작성하실 수 있습니다.
      </div>
      <div class="footer">저희 비단길을 이용해주셔서 감사합니다. 다음에는 더 쉽고 빠른 서비스로 찾아뵙겠습니다</div>

    </body>
    </html>
    """

def render_order_start_email(user_nickname, order_id):
  return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
      <meta charset="UTF-8">
      <title>주문 접수 확인</title>
      <style>
        body {{
          margin: 0;
          padding: 24px;
          background-color: #ffffff;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          color: #000000;
          line-height: 1.6;
        }}

        .header {{
          color: #3B82F6;  /* Tailwind blue-500 */
          font-size: 20px;
          font-weight: 700;
          margin-bottom: 20px;
        }}

        .section {{
          margin-bottom: 18px;
        }}

        .highlight {{
          font-weight: bold;
        }}

        a.button {{
          display: inline-block;
          padding: 10px 18px;
          color: white;
          background-color: #3B82F6;
          text-decoration: none;
          border-radius: 6px;
          margin-top: 12px;
        }}

        .footer {{
          font-size: 14px;
          color: #555;
          margin-top: 32px;
        }}
      </style>
    </head>
    <body>

      <div class="section">안녕하세요, <span class="highlight">{user_nickname}</span>님 😊</div>

      <div class="section">
        고객님의 주문 요청이 접수되었습니다.<br>
        주문번호: {order_id}<br><br>
        더 자세한 사항은 <a href="https://bidangil.co"><strong>'홈페이지</strong></a> -> 내 정보'에서 확인하실 수 있습니다.<br>
        곧 접수된 주문의 통관정보와 결제 링크를 안내드리겠습니다.<br>

      </div>
      <div class="footer">통관정보 안내는 고객님이 주문하신 물품들의 통관 제약/제한을 안내드리는 절차입니다.<br>비단길을 이용해주셔서 대단히 감사합니다.</div>

    </body>
    </html>
    """





def render_item_payment_confirm_email(user_nickname):
    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
      <meta charset="UTF-8">
      <title>주문 접수 확인</title>
      <style>
        body {{
          margin: 0;
          padding: 24px;
          background-color: #ffffff;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          color: #000000;
          line-height: 1.6;
        }}

        .header {{
          color: #3B82F6;  /* Tailwind blue-500 */
          font-size: 20px;
          font-weight: 700;
          margin-bottom: 20px;
        }}

        .section {{
          margin-bottom: 18px;
        }}

        .highlight {{
          font-weight: bold;
        }}


        .footer {{
          font-size: 14px;
          color: #555;
          margin-top: 32px;
        }}
      </style>
    </head>
    <body>

      <div class="section">안녕하세요, <span class="highlight">{user_nickname}</span>님 😊</div>

      <div class="section">
        고객님의 결제가 정상 처리되었습니다.<br>
        비단길에서 고객님의 주문을 구매한 뒤, 추후 안내드립니다.<br><br>
      </div>
      <div class="footer">저희 비단길을 이용해주셔서 대단히 감사합니다.</div>

    </body>
    </html>
    """



def render_delivery_payment_confirm_email(user_nickname):
    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
      <meta charset="UTF-8">
      <title>주문 접수 확인</title>
      <style>
        body {{
          margin: 0;
          padding: 24px;
          background-color: #ffffff;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          color: #000000;
          line-height: 1.6;
        }}

        .header {{
          color: #3B82F6;  /* Tailwind blue-500 */
          font-size: 20px;
          font-weight: 700;
          margin-bottom: 20px;
        }}

        .section {{
          margin-bottom: 18px;
        }}

        .highlight {{
          font-weight: bold;
        }}


        .footer {{
          font-size: 14px;
          color: #555;
          margin-top: 32px;
        }}
      </style>
    </head>
    <body>

      <div class="section">안녕하세요, <span class="highlight">{user_nickname}</span>님 😊</div>

      <div class="section">
        고객님의 결제가 정상 처리되었습니다.<br>
        비단길에서 고객님의 물품을 배송합니다. 배송 후에는 송장 번호와 함께 안내드립니다.<br><br>
      </div>
      <div class="footer">저희 비단길을 이용해주셔서 대단히 감사합니다.</div>

    </body>
    </html>
    """